import importlib.metadata
import typer


def version_cmd():
    """Print version and exit"""
    typer.echo(importlib.metadata.version("pious"))
