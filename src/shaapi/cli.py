"""shaapi command-line interface.

Two roles in one binary:

* **Scaffolding** — ``shaapi new "my api"`` generates a project.
* **Project runner** — from inside a generated project, domain groups wrap
  ``docker compose`` directly so the same commands work on Windows, macOS and
  Linux (no bash, no ``./docker-run.sh`` "is not recognized" on Windows)::

      shaapi up                       # lifecycle
      shaapi db generate -m "..."     # database / migrations
      shaapi db apply
      shaapi auth init                # create an admin
      shaapi storage init             # ensure the bucket exists
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shaapi import __version__, docker_ops
from shaapi.generator import (
    add_plugin,
    create_project,
    list_plugins,
    remove_plugin,
    slugify,
)

# Make output robust on Windows consoles (cp1252) and when piped.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="shaapi - scaffold and run lean, batteries-included FastAPI backends.",
)
db_app = typer.Typer(no_args_is_help=True, help="Database & migrations (Alembic).")
auth_app = typer.Typer(no_args_is_help=True, help="Authentication bootstrap.")
storage_app = typer.Typer(no_args_is_help=True, help="Object storage (MinIO / S3).")
app.add_typer(db_app, name="db")
app.add_typer(auth_app, name="auth")
app.add_typer(storage_app, name="storage")
console = Console()

_PATH_OPTION = typer.Option(Path("."), "--path", "-p", help="Project directory.")


def _docker(action, *args, **kwargs) -> None:
    """Run a docker_ops action, turning failures into a clean CLI error."""
    try:
        action(*args, **kwargs)
    except docker_ops.DockerError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1)


# --------------------------------------------------------------------------- #
# new  (scaffolding)
# --------------------------------------------------------------------------- #

def _create_project(
    name: str,
    path: Path,
    monitoring: Optional[bool],
    git: Optional[bool],
    yes: bool,
) -> None:
    slug = slugify(name)
    console.print(f"\n[bold cyan]shaapi[/] creating project [bold]{slug}[/]\n")

    if monitoring is None:
        monitoring = (
            False if yes
            else typer.confirm("Include monitoring (Prometheus/Grafana/Tempo/Loki)?", default=False)
        )
    if git is None:
        git = True if yes else typer.confirm("Initialize a git repository?", default=True)

    try:
        dest = create_project(name, path, monitoring=monitoring, git_init=git)
    except (FileExistsError, ValueError, RuntimeError) as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1)

    up_cmd = "shaapi up" + (" --monitoring" if monitoring else "")
    console.print(
        Panel.fit(
            f"[green][OK][/] Project created at [bold]{dest}[/]\n\n"
            f"[bold]Next steps[/]\n"
            f"  cd {dest.name}\n"
            f"  {up_cmd}              # build + start the stack\n"
            f"  shaapi db apply       # run migrations\n"
            f"  shaapi auth init      # create an admin to log into Swagger\n\n"
            f"Then open [cyan]http://localhost:8000/admin/api/v1/docs[/]\n"
            f"[dim](On Unix you can also use ./docker-run.sh instead of shaapi.)[/]",
            title="Done",
            border_style="cyan",
        )
    )


@app.command("new")
def new_command(
    name: str = typer.Argument(..., help='Project name, e.g. "my api".'),
    path: Path = typer.Option(Path("."), "--path", "-p", help="Where to create the project."),
    monitoring: Optional[bool] = typer.Option(
        None, "--monitoring/--no-monitoring", help="Include the Prometheus/Grafana stack."
    ),
    git: Optional[bool] = typer.Option(
        None, "--git/--no-git", help="Initialize a git repository."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Accept defaults, skip prompts."),
) -> None:
    """Create a new shaapi project."""
    _create_project(name, path, monitoring, git, yes)


@app.command("create-project", hidden=True)
def create_project_alias(
    name: str = typer.Argument(..., help='Project name, e.g. "my api".'),
    path: Path = typer.Option(Path("."), "--path", "-p"),
    monitoring: Optional[bool] = typer.Option(None, "--monitoring/--no-monitoring"),
    git: Optional[bool] = typer.Option(None, "--git/--no-git"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Deprecated alias for `shaapi new`."""
    _create_project(name, path, monitoring, git, yes)


# --------------------------------------------------------------------------- #
# db  (database & migrations)
# --------------------------------------------------------------------------- #

@db_app.command("generate")
def db_generate(
    message: str = typer.Option(..., "--message", "-m", help='e.g. "add posts table".'),
    path: Path = _PATH_OPTION,
) -> None:
    """Autogenerate a new Alembic migration from your model changes."""
    _docker(docker_ops.make_migration, message, path)
    console.print("[green][OK][/] Migration generated. Apply it with [bold]shaapi db apply[/].")


@db_app.command("apply")
def db_apply(path: Path = _PATH_OPTION) -> None:
    """Apply pending migrations (alembic upgrade head)."""
    _docker(docker_ops.apply_migrations, path)
    console.print("[green][OK][/] Migrations applied.")


@db_app.command("preview")
def db_preview(path: Path = _PATH_OPTION) -> None:
    """Print the SQL that `shaapi db apply` would run, without executing it."""
    _docker(docker_ops.preview_migrations, path)


@db_app.command("pending")
def db_pending(path: Path = _PATH_OPTION) -> None:
    """Show the current DB revision vs. the latest head."""
    _docker(docker_ops.pending_migrations, path)


@db_app.command("shell")
def db_shell(path: Path = _PATH_OPTION) -> None:
    """Open psql inside the Postgres container."""
    _docker(docker_ops.db_shell, path)


# --------------------------------------------------------------------------- #
# auth  (bootstrap)
# --------------------------------------------------------------------------- #

@auth_app.command("init")
def auth_init(
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Admin email (login)."),
    password: Optional[str] = typer.Option(None, "--password", "-w", help="Admin password."),
    path: Path = _PATH_OPTION,
) -> None:
    """Create an admin user so you can log into Swagger. Runs in the api container."""
    if not email:
        email = typer.prompt("Admin email")
    if not password:
        password = typer.prompt("Admin password", hide_input=True, confirmation_prompt=True)

    _docker(docker_ops.create_admin, email, password, path)
    console.print(
        Panel.fit(
            f"[green][OK][/] Admin ready: [bold]{email}[/]\n\n"
            f"Log in at [cyan]http://localhost:8000/admin/api/v1/docs[/]",
            title="shaapi auth init",
            border_style="cyan",
        )
    )


# --------------------------------------------------------------------------- #
# storage  (object storage)
# --------------------------------------------------------------------------- #

@storage_app.command("init")
def storage_init(path: Path = _PATH_OPTION) -> None:
    """Ensure the configured object-storage bucket exists."""
    _docker(docker_ops.storage_init, path)
    console.print("[green][OK][/] Object storage ready.")


# --------------------------------------------------------------------------- #
# Docker lifecycle verbs (wrap docker compose, cross-platform)
# --------------------------------------------------------------------------- #

@app.command("up")
def up_command(
    path: Path = _PATH_OPTION,
    monitoring: bool = typer.Option(False, "--monitoring", help="Include the Prometheus/Grafana stack."),
    prod: bool = typer.Option(False, "--prod", help="Production mode (no source bind-mount)."),
) -> None:
    """Build and start the whole stack (dev: hot-reload)."""
    _docker(docker_ops.up, path, monitoring=monitoring, prod=prod)
    console.print(
        "[green][OK][/] API: [cyan]http://localhost:8000[/]  |  "
        "Swagger: [cyan]http://localhost:8000/admin/api/v1/docs[/]\n"
        "Next: [bold]shaapi db apply[/] then [bold]shaapi auth init[/]."
    )


@app.command("down")
def down_command(
    path: Path = _PATH_OPTION,
    monitoring: bool = typer.Option(False, "--monitoring", help="Also stop the monitoring stack."),
) -> None:
    """Stop and remove the stack's containers."""
    _docker(docker_ops.down, path, monitoring=monitoring)


@app.command("logs")
def logs_command(
    service: Optional[str] = typer.Argument(None, help="Service to tail (e.g. api). Omit for all."),
    path: Path = _PATH_OPTION,
) -> None:
    """Tail container logs (Ctrl-C to stop)."""
    _docker(docker_ops.logs, path, service=service)


@app.command("restart")
def restart_command(
    service: Optional[str] = typer.Argument(None, help="Service to restart (e.g. api). Omit for all."),
    path: Path = _PATH_OPTION,
) -> None:
    """Restart containers."""
    _docker(docker_ops.restart, path, service=service)


@app.command("ps")
def ps_command(path: Path = _PATH_OPTION) -> None:
    """Show container status."""
    _docker(docker_ops.ps, path)


@app.command("shell")
def shell_command(path: Path = _PATH_OPTION) -> None:
    """Open a shell inside the api container."""
    _docker(docker_ops.shell, path)


@app.command("redis")
def redis_command(path: Path = _PATH_OPTION) -> None:
    """Open redis-cli inside the Redis container."""
    _docker(docker_ops.redis_shell, path)


# --------------------------------------------------------------------------- #
# Plugins
# --------------------------------------------------------------------------- #

@app.command("list-plugins")
def list_plugins_command() -> None:
    """List the plugins you can add to a project."""
    plugins = list_plugins()
    if not plugins:
        console.print("No plugins available.")
        return
    table = Table(title="shaapi plugins", title_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Version")
    table.add_column("Description")
    for p in plugins:
        table.add_row(p["name"], p["version"], p["summary"])
    console.print(table)
    console.print("\nAdd one with: [bold]shaapi add <name>[/]")


@app.command("add")
def add_command(
    name: str = typer.Argument(..., help="Plugin name (see `shaapi list-plugins`)."),
    path: Path = _PATH_OPTION,
) -> None:
    """Add a plugin to the current project (copies it into backend/plugins/)."""
    try:
        res = add_plugin(name, path)
    except (FileExistsError, ValueError, RuntimeError) as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1)

    lines = [f"[green][OK][/] Added plugin [bold]{name}[/] -> {res['dest']}"]
    if res.get("added_deps"):
        deps = " ".join(res["added_deps"])
        if res.get("locked"):
            lines.append(f"\n[green]Added dependencies[/] ({deps}) and refreshed uv.lock.")
        else:
            lines.append(
                f"\n[yellow]Added dependencies[/] ({deps}) to pyproject.toml.\n"
                f"Run [bold]uv lock[/] to refresh the lockfile before building."
            )
    if res["message"]:
        lines.append(f"\n{res['message']}")
    lines.append("\nRestart the API to load it: [bold]shaapi restart api[/]")
    console.print(Panel.fit("\n".join(lines), title="shaapi add", border_style="cyan"))


@app.command("remove")
def remove_command(
    name: str = typer.Argument(..., help="Installed plugin name."),
    path: Path = _PATH_OPTION,
) -> None:
    """Remove a plugin from the current project."""
    try:
        dest = remove_plugin(name, path)
    except (FileNotFoundError, RuntimeError) as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1)
    console.print(f"[green][OK][/] Removed plugin [bold]{name}[/] ({dest})")


# --------------------------------------------------------------------------- #
# Meta
# --------------------------------------------------------------------------- #

def _version_callback(value: bool) -> None:
    if value:
        console.print(f"shaapi {__version__}")
        raise typer.Exit()


@app.command()
def version() -> None:
    """Show the shaapi version."""
    console.print(f"shaapi {__version__}")


@app.callback()
def main(
    _version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """shaapi CLI."""


if __name__ == "__main__":
    app()
