import typer
from typing_extensions import Annotated
from pathlib import Path
from ..flops import Flops

app = typer.Typer(help="Utility module for filtering and printing flop subsets")


@app.command()
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
        typer.echo(f'{len(flops)} flops satisfy filter "{filter_expr}"')
    if file is not None:
        with open(file, "w+") as f:
            f.write(str(flops))


# Legacy argparse compatibility
from argparse import Namespace, _SubParsersAction


def exec_flops(args: Namespace):
    flops_cmd(
        filter_expr=args.filter,
        count=args.count,
        file=Path(args.file) if args.file else None,
    )


def register_command(sub_parsers: _SubParsersAction):
    parser_flops = sub_parsers.add_parser(
        "flops", description="Utility module for filtering and printing flop subsets"
    )
    parser_flops.set_defaults(function=exec_flops)

    parser_flops.add_argument(
        "filter",
        nargs="?",
        help="Filter flops based on texture, e.g., 'not flush and straight'",
    )
    parser_flops.add_argument(
        "--count", action="store_true", help="Print number of flops satisfying filter"
    )
    parser_flops.add_argument("--file", "-f", help="print flops to file")
