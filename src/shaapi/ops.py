"""shaops — production tooling for shaapi projects.

Generates hardened production artifacts (a docker-compose overlay that keeps the
datastores off the public network, plus VPS provisioning/firewall scripts) and
strong secrets. All generation, no remote execution: shaops writes files you run
yourself on the server, so nothing reaches out and no credentials are handled
over the wire.

Kept dependency-free (pure stdlib) so the CLI stays tiny.
"""
from __future__ import annotations

import os
import secrets as _secrets
from pathlib import Path

from shaapi.generator import find_project_root, write_prod_artifacts


class OpsError(RuntimeError):
    """A shaops operation could not be completed."""


# Secrets that must be replaced before a production boot (see the conf.py guard).
_SECRET_KEYS = ("TOKEN_SECRET_KEY", "OPERA_LOG_ENCRYPT_SECRET_KEY",
                "POSTGRES_PASSWORD", "MINIO_SECRET_KEY")


def _require_root(path: Path | str) -> Path:
    root = find_project_root(path)
    if root is None:
        raise OpsError(
            "Not inside a shaapi project (no backend/ + pyproject.toml found). "
            "cd into your project first."
        )
    return root


def generate_secrets() -> dict[str, str]:
    """Return a fresh set of strong production secrets/credentials."""
    return {
        "TOKEN_SECRET_KEY": _secrets.token_urlsafe(32),
        "OPERA_LOG_ENCRYPT_SECRET_KEY": os.urandom(32).hex(),
        "POSTGRES_PASSWORD": _secrets.token_urlsafe(24),
        "MINIO_SECRET_KEY": _secrets.token_urlsafe(24),
    }


def harden(path: Path | str = ".") -> list[Path]:
    """Write the production artifacts into the project; return the files written."""
    root = _require_root(path)
    return write_prod_artifacts(root, root.name)


def write_secrets_to_env(path: Path | str, secrets: dict[str, str]) -> Path:
    """Set each KEY=value in the project's ``.env`` (creating the file if absent).

    Existing matching keys are replaced in place; missing ones are appended.
    Other lines are left untouched.
    """
    root = _require_root(path)
    env = root / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in secrets:
                out.append(f"{key}={secrets[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key, value in secrets.items():
        if key not in seen:
            out.append(f"{key}={value}")
    env.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    return env


CHECKLIST = """[bold cyan]shaapi production go-live checklist[/]

[bold]On the server (one-time)[/]
  1. [bold]bash deploy/provision.sh[/]   install Docker Engine + compose
  2. [bold]bash deploy/harden-os.sh[/]   firewall: deny inbound except 22/80/443

[bold]Config[/]
  3. [bold]cp .env.prod.example .env[/]
  4. [bold]shaapi ops secrets --write[/] generate + inject real secrets
  5. set POSTGRES_PASSWORD / MINIO_SECRET_KEY, and DB_AUTO_CREATE=false

[bold]Run[/]
  6. [bold]shaapi up --prod[/]           datastores stay OFF the public network
  7. [bold]shaapi db apply[/]            run migrations
  8. [bold]shaapi auth init[/]           create the first admin

[bold]Verify[/]
  9. [bold]ss -tulnp | grep -E ':(5432|9000)'[/]  -> nothing on 0.0.0.0
 10. reverse proxy (nginx/Caddy) terminates TLS on 443 -> 127.0.0.1:8000
 11. [bold]shaapi sec audit[/]           (coming in 0.3.0) automated security audit
"""
