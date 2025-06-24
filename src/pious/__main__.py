import typer
from typing_extensions import Annotated

# Import all command modules to register them
from ._executables import (
    aggregate,
    blockers,
    conf,
    flops,
    lines,
    version,
    view_agg_report,
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
    invoke_without_command=True,
)

# Add all subcommands
app.command(name="aggregate")(aggregate.aggregate_cmd)
app.command(name="view-agg-report")(view_agg_report.aggregation_viewer_cmd)
app.command(name="blockers")(blockers.blockers_cmd)
app.command(name="conf")(conf.conf_cmd)
app.command(name="flops")(flops.flops_cmd)
app.command(name="lines")(lines.lines_cmd)
app.command(name="version")(version.version_cmd)


def main():
    app()


if __name__ == "__main__":
    main()
