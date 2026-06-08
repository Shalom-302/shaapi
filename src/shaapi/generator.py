"""Project scaffolding: copy the bundled template into a new project, rebranding
the ``shaapi`` identifier to the user's project name.

Kept intentionally dependency-free (pure stdlib) so the ``shaapi`` CLI stays
tiny — the heavy stack lives only in the generated project.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"

# Path components never copied into a generated project.
_EXCLUDE_NAMES = {
    "__pycache__", ".venv", "venv", ".git", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", "node_modules", ".env", ".DS_Store",
}
# Suffixes never copied at all (local dev artifacts).
_SKIP_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite3", ".log"}
# Binary files: copied verbatim, never text-substituted.
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".xdb",
    ".woff", ".woff2", ".ttf", ".pdf", ".zip", ".gz",
}


def slugify(name: str) -> str:
    """Turn a project name into a safe lowercase identifier slug."""
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise ValueError("Project name must contain at least one letter or digit.")
    if slug[0].isdigit():
        slug = f"app_{slug}"
    return slug


def _rebrand(text: str, slug: str) -> str:
    """Replace the shaapi identifier with the project slug, preserving case."""
    text = text.replace("SHAAPI", slug.upper())
    text = text.replace("Shaapi", slug.capitalize())
    text = text.replace("shaapi", slug)
    return text


def create_project(
    name: str,
    dest_parent: Path | str,
    *,
    monitoring: bool = False,
    git_init: bool = True,
) -> Path:
    """Generate a new shaapi project and return its path.

    :param name: human project name (e.g. "My API").
    :param dest_parent: directory in which the project folder is created.
    :param monitoring: include the opt-in Prometheus/Grafana stack.
    :param git_init: run ``git init`` in the new project.
    """
    if not TEMPLATE_DIR.is_dir():
        raise RuntimeError(f"Template not found at {TEMPLATE_DIR}")

    slug = slugify(name)
    dest = Path(dest_parent).resolve() / slug
    if dest.exists():
        raise FileExistsError(f"Directory already exists: {dest}")

    for src in sorted(TEMPLATE_DIR.rglob("*")):
        rel = src.relative_to(TEMPLATE_DIR)
        if any(part in _EXCLUDE_NAMES for part in rel.parts):
            continue
        if src.is_dir():
            continue
        if src.suffix in _SKIP_SUFFIXES:
            continue
        # Monitoring is opt-in: drop its compose file and the etc/ configs.
        if not monitoring and (
            src.name == "docker-compose.monitoring.yml" or rel.parts[0] == "etc"
        ):
            continue

        target = dest / Path(_rebrand(str(rel), slug))
        target.parent.mkdir(parents=True, exist_ok=True)

        if src.suffix in _BINARY_SUFFIXES:
            shutil.copy2(src, target)
            continue
        try:
            content = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src, target)
            continue
        # Force LF: the generated project targets Linux/Docker, and CRLF would
        # break shell scripts and .env files inside containers. newline="\n"
        # disables Windows' \n -> \r\n translation.
        target.write_text(_rebrand(content, slug), encoding="utf-8", newline="\n")

    # Seed a ready-to-run .env from the template.
    env_template = dest / ".env.template"
    env_file = dest / ".env"
    if env_template.exists() and not env_file.exists():
        env_file.write_text(
            env_template.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )

    if git_init:
        try:
            subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            pass  # git is optional; never fail project creation over it

    return dest
