"""shaapi command-line interface."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from shaapi import __version__
from shaapi.generator import create_project, slugify

# Make output robust on Windows consoles (cp1252) and when piped.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="shaapi - scaffold lean, batteries-included FastAPI backends.",
)
console = Console()


@app.command("create-project")
def create_project_command(
    name: str = typer.Argument(..., help='Project name, e.g. "my api".'),
    path: Path = typer.Option(Path("."), "--path", "-p", help="Where to create the project."),
    monitoring: Optional[bool] = typer.Option(
        None, "--monitoring/--no-monitoring", help="Include the Prometheus/Grafana stack."
    ),
    git: Optional[bool] = typer.Option(
        None, "--git/--no-git", help="Initialize a git repository."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Accept defaults, skip prompts."),
):
    """Create a new shaapi project."""
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

    up_cmd = "./docker-run.sh up" + (" --monitoring" if monitoring else "")
    console.print(
        Panel.fit(
            f"[green][OK][/] Project created at [bold]{dest}[/]\n\n"
            f"[bold]Next steps[/]\n"
            f"  cd {dest.name}\n"
            f"  {up_cmd}\n\n"
            f"Then open [cyan]http://localhost:8000/admin/api/v1/docs[/]",
            title="Done",
            border_style="cyan",
        )
    )


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
