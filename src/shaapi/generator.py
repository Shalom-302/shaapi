"""Project scaffolding: copy the bundled template into a new project, rebranding
the ``shaapi`` identifier to the user's project name.

Kept intentionally dependency-free (pure stdlib) so the ``shaapi`` CLI stays
tiny — the heavy stack lives only in the generated project.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tomllib
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "template"
PLUGINS_DIR = Path(__file__).resolve().parent / "plugins"

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


# --------------------------------------------------------------------------- #
# Plugins
# --------------------------------------------------------------------------- #

def list_plugins() -> list[dict]:
    """Return the catalog of plugins bundled with shaapi."""
    out: list[dict] = []
    if not PLUGINS_DIR.is_dir():
        return out
    for d in sorted(PLUGINS_DIR.iterdir()):
        manifest = d / "plugin.toml"
        if not manifest.is_file():
            continue
        meta = tomllib.loads(manifest.read_text(encoding="utf-8")).get("plugin", {})
        out.append(
            {
                "name": meta.get("name", d.name),
                "summary": meta.get("summary", ""),
                "version": meta.get("version", ""),
            }
        )
    return out


def _find_project_root(start: Path | str) -> Path | None:
    """Walk up from *start* to find a shaapi project (backend/ + pyproject.toml)."""
    p = Path(start).resolve()
    for cand in [p, *p.parents]:
        if (cand / "backend").is_dir() and (cand / "pyproject.toml").is_file():
            return cand
    return None


def add_plugin(name: str, project_dir: Path | str = ".") -> dict:
    """Copy a catalog plugin into a project's backend/plugins/<name>/."""
    src = PLUGINS_DIR / name
    manifest = src / "plugin.toml"
    if not manifest.is_file():
        raise ValueError(f"Unknown plugin '{name}'. Run `shaapi list-plugins`.")

    root = _find_project_root(project_dir)
    if root is None:
        raise RuntimeError(
            "Not inside a shaapi project (no backend/ + pyproject.toml found). "
            "cd into your project first."
        )

    dest = root / "backend" / "plugins" / name
    if dest.exists():
        raise FileExistsError(f"Plugin '{name}' is already installed at {dest}")

    # Ensure backend/plugins is a package.
    plugins_pkg = root / "backend" / "plugins"
    plugins_pkg.mkdir(parents=True, exist_ok=True)
    init = plugins_pkg / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8", newline="\n")

    files_dir = src / "files"
    for f in files_dir.rglob("*"):
        if f.is_dir():
            continue
        target = dest / f.relative_to(files_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix in _BINARY_SUFFIXES:
            shutil.copy2(f, target)
        else:
            target.write_text(f.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    meta = tomllib.loads(manifest.read_text(encoding="utf-8"))
    packages = meta.get("dependencies", {}).get("packages", [])
    added = _add_deps_to_pyproject(root, packages)
    locked = _uv_lock(root) if added else None
    return {
        "name": name,
        "dest": dest,
        "packages": packages,
        "added_deps": added,
        "locked": locked,
        "message": meta.get("post_add", {}).get("message", ""),
    }


def _add_deps_to_pyproject(root: Path, packages: list[str]) -> list[str]:
    """Append missing packages to the project's [project].dependencies array.

    Returns the packages that were actually added. Best-effort text insertion
    (preserves the file); no-op for packages already present.
    """
    if not packages:
        return []
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Locate the `dependencies = [` ... `]` block.
    start = next((i for i, ln in enumerate(lines) if ln.strip().startswith("dependencies = [")), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "]"), None)
    if end is None:
        return []
    existing = "\n".join(lines[start:end]).lower()
    added = []
    insert_at = end
    for pkg in packages:
        bare = re.split(r"[<>=!~ \[]", pkg, 1)[0].lower()
        if bare and bare not in existing:
            lines.insert(insert_at, f'    "{pkg}",')
            insert_at += 1
            added.append(pkg)
    if added:
        pyproject.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return added


def _uv_lock(root: Path) -> bool:
    """Run `uv lock` in the project to refresh uv.lock. Returns True on success."""
    for cmd in (["uv", "lock"], ["python", "-m", "uv", "lock"]):
        try:
            subprocess.run(cmd, cwd=root, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
    return False


def remove_plugin(name: str, project_dir: Path | str = ".") -> Path:
    """Remove an installed plugin from a project."""
    root = _find_project_root(project_dir)
    if root is None:
        raise RuntimeError("Not inside a shaapi project.")
    dest = root / "backend" / "plugins" / name
    if not dest.exists():
        raise FileNotFoundError(f"Plugin '{name}' is not installed.")
    shutil.rmtree(dest)
    return dest
