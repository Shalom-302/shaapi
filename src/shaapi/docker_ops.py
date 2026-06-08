"""Cross-platform Docker orchestration for shaapi projects.

The host ``shaapi`` command wraps ``docker compose`` directly (no bash), so the
same commands work on Windows, macOS and Linux — solving the classic Windows
"``docker-run.sh`` is not recognized" problem. The bundled ``docker-run.sh``
remains for shell users on Unix.

Kept dependency-free (pure stdlib + subprocess) so the CLI stays tiny.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from shaapi.generator import find_project_root


class DockerError(RuntimeError):
    """A docker/compose invocation failed, or the project could not be found."""


# --------------------------------------------------------------------------- #
# Compose discovery & composition
# --------------------------------------------------------------------------- #

def _compose_cmd() -> list[str]:
    """Return the compose invocation prefix (``docker compose`` preferred)."""
    if shutil.which("docker"):
        try:
            subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                check=True,
            )
            return ["docker", "compose"]
        except (subprocess.CalledProcessError, OSError):
            pass
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    raise DockerError(
        "Docker Compose not found. Install Docker Desktop or the compose plugin."
    )


def _require_root(path: Path | str) -> Path:
    root = find_project_root(path)
    if root is None:
        raise DockerError(
            "Not inside a shaapi project (no backend/ + pyproject.toml found). "
            "cd into your project first."
        )
    return root


def _running_services(root: Path) -> set[str] | None:
    """Names of services currently running, or None if it can't be determined."""
    try:
        proc = subprocess.run(
            _compose_cmd() + ["-f", str(root / "docker-compose.yml"),
                              "ps", "--services", "--status", "running"],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except (OSError, DockerError):
        return None
    if proc.returncode != 0:
        return None
    return {s.strip() for s in proc.stdout.splitlines() if s.strip()}


def _require_running(path: Path | str, service: str) -> Path:
    """Resolve the project root and fail early if *service* isn't up.

    Most management commands (auth/storage/db) ``exec`` into a running
    container, so this turns the meticulous ordering — ``shaapi up`` *before*
    ``shaapi auth init`` — into a clear, actionable error instead of a cryptic
    Docker failure.
    """
    root = _require_root(path)
    running = _running_services(root)
    if running is not None and service not in running:
        raise DockerError(
            f"The '{service}' container is not running. "
            f"Start the stack first with `shaapi up`."
        )
    return root


def _ensure_env(root: Path) -> None:
    """Create ``.env`` from ``.env.template`` on first run (mirrors docker-run.sh)."""
    env = root / ".env"
    tmpl = root / ".env.template"
    if not env.exists() and tmpl.exists():
        env.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def _compose_files(root: Path, *, monitoring: bool, prod: bool) -> list[str]:
    files = ["-f", str(root / "docker-compose.yml")]
    if not prod:
        override = root / "docker-compose.override.yml"
        if override.exists():
            files += ["-f", str(override)]
    if monitoring:
        mon = root / "docker-compose.monitoring.yml"
        if not mon.exists():
            raise DockerError(
                "This project was generated without monitoring. Re-create it with "
                "`shaapi create project <name> --monitoring`."
            )
        files += ["-f", str(mon)]
    return files


def _base(path: Path | str, *, monitoring: bool, prod: bool) -> tuple[list[str], Path]:
    root = _require_root(path)
    _ensure_env(root)
    return _compose_cmd() + _compose_files(root, monitoring=monitoring, prod=prod), root


def _env_value(root: Path, key: str, default: str) -> str:
    """Read a single ``KEY=value`` from the project's ``.env`` (best-effort)."""
    env = root / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line.split("=", 1)[0].strip() == key:
                return line.split("=", 1)[1].strip()
    return default


def _run(
    extra: list[str],
    path: Path | str = ".",
    *,
    monitoring: bool = False,
    prod: bool = False,
    check: bool = True,
) -> int:
    cmd, root = _base(path, monitoring=monitoring, prod=prod)
    full = cmd + extra
    proc = subprocess.run(full, cwd=root)
    if check and proc.returncode != 0:
        raise DockerError(f"`{' '.join(extra)}` failed (exit {proc.returncode}).")
    return proc.returncode


# --------------------------------------------------------------------------- #
# High-level operations (one per shaapi verb)
# --------------------------------------------------------------------------- #

def up(path: Path | str = ".", *, monitoring: bool = False, prod: bool = False) -> None:
    _run(["up", "-d", "--build"], path, monitoring=monitoring, prod=prod)


def down(path: Path | str = ".", *, monitoring: bool = False) -> None:
    _run(["down"], path, monitoring=monitoring)


def logs(path: Path | str = ".", *, service: str | None = None) -> None:
    extra = ["logs", "-f"] + ([service] if service else [])
    _run(extra, path, check=False)


def restart(path: Path | str = ".", *, service: str | None = None) -> None:
    extra = ["restart"] + ([service] if service else [])
    _run(extra, path)


def ps(path: Path | str = ".") -> None:
    _run(["ps"], path, check=False)


def shell(path: Path | str = ".") -> None:
    _require_running(path, "api")
    _run(["exec", "api", "bash"], path, check=False)


def db_shell(path: Path | str = ".") -> None:
    root = _require_running(path, "postgres")
    user = _env_value(root, "POSTGRES_USER", "postgres")
    database = _env_value(root, "POSTGRES_DATABASE", "shaapi")
    _run(["exec", "postgres", "psql", "-U", user, "-d", database], path, check=False)


def redis_shell(path: Path | str = ".") -> None:
    _require_running(path, "redis")
    _run(["exec", "redis", "redis-cli"], path, check=False)


def _alembic(subcmd: str, path: Path | str = ".", *, check: bool = True) -> None:
    """Run an alembic subcommand from the backend/ dir inside the api container."""
    _require_running(path, "api")
    _run(["exec", "api", "bash", "-c", f"cd backend && alembic {subcmd}"], path, check=check)


def apply_migrations(path: Path | str = ".") -> None:
    """``alembic upgrade head`` inside the api container."""
    _alembic("upgrade head", path)


def make_migration(message: str, path: Path | str = ".") -> None:
    """Autogenerate a new Alembic revision inside the api container."""
    safe = message.replace("'", "")  # the message is wrapped in single quotes below
    _alembic(f"revision --autogenerate -m '{safe}'", path)


def preview_migrations(path: Path | str = ".") -> None:
    """Print the SQL that ``shaapi db apply`` would run, without executing it."""
    _alembic("upgrade head --sql", path)


def pending_migrations(path: Path | str = ".") -> None:
    """Show the current DB revision vs. the latest head (a mismatch = pending)."""
    _alembic(
        "current && echo '--- latest head(s) ---' && alembic heads",
        path,
        check=False,
    )


def create_admin(email: str, password: str, path: Path | str = ".") -> None:
    """Run the in-container admin bootstrap (``backend.cli create-admin``)."""
    _require_running(path, "api")
    _run(
        ["exec", "api", "python", "-m", "backend.cli",
         "create-admin", "--email", email, "--password", password],
        path,
    )


def storage_init(path: Path | str = ".") -> None:
    """Ensure the configured object-storage bucket exists (``backend.cli storage-init``)."""
    _require_running(path, "api")
    _run(["exec", "api", "python", "-m", "backend.cli", "storage-init"], path)
