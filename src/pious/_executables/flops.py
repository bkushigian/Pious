import typer
from typing_extensions import Annotated
from pathlib import Path
from ..flops import Flops


def flops_cmd(
    filter_expr: Annotated[
        str,
        typer.Argument(
            help="Filter flops based on texture, e.g., 'not flush and straight'"
        ),
    ] = None,
    count: Annotated[
        bool, typer.Option(help="Print number of flops satisfying filter")
    ] = False,
    file: Annotated[Path, typer.Option(help="Output file path")] = None,
):
    """Filter and print flop subsets"""
    flops = Flops()

    if filter_expr is not None:
        flops.filter(filter_expr)
    typer.echo(str(flops))
    if count:
        if filter_expr is None:
            typer.echo(f"{len(flops)} flops in total")
        else:
            typer.echo(f'{len(flops)} flops satisfy filter "{filter_expr}"')
    if file is not None:
        with open(file, "w+") as f:
            f.write(str(flops))
