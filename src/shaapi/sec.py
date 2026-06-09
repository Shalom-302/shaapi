"""shasec — security testing for shaapi projects (pure stdlib, no extra deps).

Two modes:

* **static** — audit a project's config/code for known weaknesses
  (``shaapi sec audit``).
* **dynamic** — probe a running API: auth attacks, header/route scan, port
  reachability (``shaapi sec auth`` / ``scan`` / ``ports``).

The dynamic checks are deliberately black-box and dependency-free (urllib +
hmac), so shasec can be pointed at any HTTP API, not just shaapi. Heavier
tooling (nuclei / zap / sqlmap) plugs in later as optional plugins.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import socket
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from shaapi.generator import find_project_root

# Severity ranking (higher = worse) — drives sorting and the CI exit code.
SEVERITY = {"PASS": 0, "INFO": 1, "LOW": 2, "MEDIUM": 3, "HIGH": 4, "CRITICAL": 5}
FAIL_AT = SEVERITY["HIGH"]  # exit non-zero when any finding is >= this

# Development defaults shipped by the shaapi template.
DEFAULT_TOKEN_SECRET = "dev-insecure-change-me-token-secret-key"
DEFAULT_OPERA_SECRET = "dev-insecure-change-me-opera-log-key"
_DEFAULT_PAIRS = {
    "TOKEN_SECRET_KEY": DEFAULT_TOKEN_SECRET,
    "OPERA_LOG_ENCRYPT_SECRET_KEY": DEFAULT_OPERA_SECRET,
    "POSTGRES_PASSWORD": "postgres",
    "MINIO_SECRET_KEY": "minioadmin",
}

# Security response headers we expect a hardened API (or its proxy) to set.
SECURITY_HEADERS = {
    "Strict-Transport-Security": "MEDIUM",
    "X-Content-Type-Options": "LOW",
    "X-Frame-Options": "LOW",
    "Content-Security-Policy": "LOW",
}


class SecError(RuntimeError):
    """A shasec operation could not be completed."""


@dataclass
class Finding:
    severity: str
    title: str
    detail: str = ""
    remediation: str = ""

    @property
    def rank(self) -> int:
        return SEVERITY.get(self.severity, 0)


# --------------------------------------------------------------------------- #
# Static audit
# --------------------------------------------------------------------------- #

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _env_values(root: Path) -> dict[str, str]:
    """Parse ``KEY=value`` from .env (falling back to .env.template)."""
    for name in (".env", ".env.template"):
        f = root / name
        if f.exists():
            out: dict[str, str] = {}
            for line in _read(f).splitlines():
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, v = s.split("=", 1)
                    out[k.strip()] = v.strip()
            return out
    return {}


def _git_tracked(root: Path, rel: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=root, capture_output=True, text=True,
        )
        return r.returncode == 0
    except (OSError, FileNotFoundError):
        return False


def audit_project(path: Path | str = ".") -> list[Finding]:
    """Static audit of a shaapi project. Returns findings (worst-first sorting
    is done by the caller)."""
    root = find_project_root(path)
    if root is None:
        raise SecError(
            "Not inside a shaapi project (no backend/ + pyproject.toml found). "
            "cd into your project first."
        )
    findings: list[Finding] = []
    env = _env_values(root)
    backend = root / "backend"
    conf = _read(backend / "core" / "conf.py")
    registrar = _read(backend / "core" / "registrar.py")
    auth_service = _read(backend / "app" / "admin" / "service" / "auth_service.py")

    # 1. Default secrets still in use
    for key, default in _DEFAULT_PAIRS.items():
        if env.get(key, "") == default:
            findings.append(Finding(
                "CRITICAL", f"Default secret in use: {key}",
                f"{key}={default!r} — a publicly-known development default.",
                "Set a strong value (shaapi ops secrets --write).",
            ))

    # 2. .env committed to git
    if _git_tracked(root, ".env"):
        findings.append(Finding(
            "CRITICAL", ".env is tracked by git",
            "Committing .env leaks every secret into history.",
            "git rm --cached .env, then rotate the secrets.",
        ))

    # 3. Committed credentials in seed files
    seed_dir = backend / "seeder" / "json"
    if seed_dir.is_dir():
        for jf in sorted(seed_dir.glob("*.json")):
            if re.search(r'"password"\s*:', _read(jf)):
                findings.append(Finding(
                    "HIGH", f"Committed credentials in seed: {jf.name}",
                    "A password/hash in a committed seed is a backdoor.",
                    "Remove it; create the first admin with shaapi auth init.",
                ))

    # 4. Base compose publishes datastore ports
    base_compose = _read(root / "docker-compose.yml")
    for svc, port in (("Postgres", "5432"), ("MinIO", "9000"), ("MinIO console", "9001")):
        if re.search(rf'-\s*"[^"]*:{port}"', base_compose):
            findings.append(Finding(
                "HIGH", f"Base compose publishes {svc} port {port}",
                "Datastores should stay on the internal network in the base file.",
                "Move the mapping to docker-compose.override.yml (dev only).",
            ))

    # 5. CORS wildcard with credentials
    if re.search(r"allow_origins\s*=\s*\[\s*['\"]\*['\"]", conf) and "allow_credentials=True" in registrar:
        findings.append(Finding(
            "HIGH", "CORS allows '*' together with credentials",
            "A wildcard origin plus credentials lets any site call the API as the user.",
            "Pin CORS_ALLOWED_ORIGINS to your front-end origin(s).",
        ))

    # 6. Container runs as root
    dockerfile = _read(root / "Dockerfile")
    if dockerfile and not re.search(r"(?m)^\s*USER\s+\S", dockerfile):
        findings.append(Finding(
            "MEDIUM", "Container runs as root",
            "No USER directive in the Dockerfile.",
            "Add a non-root USER to limit the blast radius of an RCE.",
        ))

    # 7. Weak cookie flags
    if "samesite='none'" in auth_service and "secure=" not in auth_service:
        findings.append(Finding(
            "MEDIUM", "Refresh-token cookie uses SameSite=None without Secure",
            "SameSite=None requires Secure; otherwise the cookie travels over plain HTTP.",
            "Set secure=True and samesite='lax' (auto-hardened outside dev).",
        ))

    # 8. API docs not gated by environment
    if registrar and "docs_url" in registrar:
        gated = ("docs_url=None" in registrar
                 or "_expose_docs" in registrar
                 or re.search(r"ENVIRONMENT\s*!=\s*['\"]prod['\"]", registrar))
        if not gated:
            findings.append(Finding(
                "MEDIUM", "API docs are not disabled in production",
                "Swagger/OpenAPI appear to be always served.",
                "Gate docs_url/openapi_url on ENVIRONMENT != 'prod'.",
            ))

    # 9. External geo-IP lookup enabled
    if re.search(r"IP_LOCATION_PARSE.*=.*['\"]online['\"]", conf):
        findings.append(Finding(
            "LOW", "External geo-IP lookup enabled by default",
            "IP_LOCATION_PARSE='online' sends each client IP to ip-api.com over HTTP.",
            "Default to 'false' (privacy + no external dependency).",
        ))

    # 10. Production fail-fast guard present?
    has_guard = "model_validator" in conf and "insecure" in conf.lower()
    if has_guard:
        findings.append(Finding(
            "PASS", "Production fail-fast guard present",
            "conf.py refuses to boot with default secrets outside dev.",
        ))
    else:
        findings.append(Finding(
            "HIGH", "No production fail-fast guard",
            "Nothing stops a prod boot while default secrets remain.",
            "Add a model_validator on Settings that raises outside dev.",
        ))

    return findings


# --------------------------------------------------------------------------- #
# HTTP helpers (urllib, dependency-free)
# --------------------------------------------------------------------------- #

@dataclass
class Resp:
    status: int
    headers: dict[str, str]
    body: str


def http(method: str, url: str, *, headers: dict | None = None,
         data: dict | None = None, timeout: float = 8.0) -> Resp:
    h = {"User-Agent": "shaapi-sec"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return Resp(r.status, dict(r.headers), r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return Resp(e.code, dict(e.headers), e.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, OSError, ssl.SSLError) as e:
        raise SecError(f"Cannot reach {url}: {e}")


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def forge_jwt(secret: str, sub: str = "1", exp_offset: int = 3600) -> str:
    """Forge an HS256 JWT signed with *secret* (stdlib hmac).

    Used to test whether a server trusts tokens signed with a known/default
    secret. A stateless API that validates the signature alone will accept it;
    one that also tracks tokens server-side (like shaapi via Redis) will not.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": sub, "exp": int(time.time()) + exp_offset}
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(sig)}"


# --------------------------------------------------------------------------- #
# Dynamic checks
# --------------------------------------------------------------------------- #

def audit_auth(base_url: str) -> list[Finding]:
    """Black-box authentication probes against a running API base URL, e.g.
    ``http://localhost:8000/admin/api/v1``."""
    base = base_url.rstrip("/")
    findings: list[Finding] = []

    # OpenAPI publicly readable?
    try:
        oa = http("GET", base + "/openapi")
        if oa.status == 200:
            findings.append(Finding(
                "LOW", "OpenAPI schema is publicly readable",
                f"GET {base}/openapi -> 200 (full API surface disclosed).",
                "Disable docs/openapi in production (ENVIRONMENT=prod).",
            ))
    except SecError:
        pass

    # 1. Token forged with the DEFAULT secret
    forged = forge_jwt(DEFAULT_TOKEN_SECRET)
    me = http("GET", base + "/auth/me", headers={"Authorization": f"Bearer {forged}"})
    if me.status == 200:
        findings.append(Finding(
            "CRITICAL", "Server accepts a token forged with the DEFAULT secret",
            f"GET /auth/me -> 200 with a JWT signed by '{DEFAULT_TOKEN_SECRET}'.",
            "Set a real TOKEN_SECRET_KEY immediately and rotate it.",
        ))
    else:
        findings.append(Finding(
            "PASS", "Forged default-secret token rejected",
            f"GET /auth/me -> {me.status} (server-side token store or non-default secret).",
        ))

    # 2. Protected route reachable without auth?
    anon = http("GET", base + "/auth/me")
    if anon.status == 200:
        findings.append(Finding(
            "HIGH", "/auth/me is reachable without authentication",
            "GET /auth/me -> 200 with no token.",
            "Require the JWT dependency/middleware on protected routes.",
        ))
    else:
        findings.append(Finding(
            "PASS", "Protected route requires authentication",
            f"GET /auth/me (no token) -> {anon.status}.",
        ))

    # 3. Login brute-force protection
    codes = [
        http("POST", base + "/auth/login",
             data={"email": "sec@probe.invalid", "password": "wrong"}).status
        for _ in range(6)
    ]
    if 429 in codes:
        findings.append(Finding(
            "PASS", "Login is rate-limited",
            f"6 rapid attempts -> {codes} (429 = throttled).",
        ))
    else:
        findings.append(Finding(
            "HIGH", "Login has no rate limit (brute-forceable)",
            f"6 rapid attempts -> {codes}; never throttled.",
            "Add a RateLimiter dependency on /auth/login.",
        ))

    return findings


def scan_api(url: str) -> list[Finding]:
    """Generic dynamic scan: security headers + OpenAPI surface."""
    u = url.rstrip("/")
    resp = http("GET", u)
    present = {k.lower() for k in resp.headers}
    findings = [
        Finding(sev, f"Missing security header: {header}",
                f"The response from {u} does not set {header}.",
                f"Add {header} via a middleware or the reverse proxy.")
        for header, sev in SECURITY_HEADERS.items()
        if header.lower() not in present
    ]
    try:
        oa = http("GET", u + "/openapi")
        if oa.status == 200:
            paths = json.loads(oa.body).get("paths", {})
            findings.append(Finding(
                "INFO", f"OpenAPI exposes {len(paths)} path(s)",
                f"GET {u}/openapi -> 200.",
                "Disable in production (ENVIRONMENT=prod).",
            ))
    except (SecError, ValueError):
        pass
    return findings


def _tcp_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def scan_ports(host: str = "localhost") -> list[Finding]:
    """Check whether the stack's datastore ports are reachable on *host*."""
    targets = [
        ("api", 8000, "INFO"),
        ("Postgres", 5432, "HIGH"),
        ("Redis", 6379, "HIGH"),
        ("MinIO", 9000, "HIGH"),
        ("MinIO console", 9001, "MEDIUM"),
    ]
    findings: list[Finding] = []
    for name, port, sev in targets:
        if _tcp_open(host, port):
            findings.append(Finding(
                "INFO" if name == "api" else sev,
                f"{name} port {port} is OPEN on {host}",
                f"TCP connect to {host}:{port} succeeded.",
                "" if name == "api"
                else "Datastores should be internal-only — run prod with `shaapi up --prod`.",
            ))
        else:
            findings.append(Finding(
                "PASS", f"{name} port {port} is closed on {host}",
                f"TCP connect to {host}:{port} refused/timed out.",
            ))
    return findings
