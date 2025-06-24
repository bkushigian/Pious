import typer
from typing_extensions import Annotated

# Import all command modules to register them
from ._executables import (
    aggregate,
    aggregation_viewer,
    blockers,
    conf,
    flops,
    lines,
    version,
)

PIOUS_DESCRIPTION = """Pious: The PIO Utility Suite

The Pious Library began as a wrapper around PioSOLVER's Universal Poker
Interface (UPI) and has evolved in to a full fledged poker software utility
suite.
"""

# Create the main Typer app
app = typer.Typer(
    name="pious",
    help="The PioSOLVER Utility Suite",
    no_args_is_help=True,
)

# Add all subcommands
app.add_typer(aggregate.app, name="aggregate")
app.add_typer(aggregation_viewer.app, name="aggregation-viewer")
app.add_typer(blockers.app, name="blockers")
app.add_typer(conf.app, name="conf")
app.add_typer(flops.app, name="flops")
app.add_typer(lines.app, name="lines")
app.add_typer(version.app, name="version")


def main():
    app()


if __name__ == "__main__":
    main()
