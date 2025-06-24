"""
This module implements an executable interface for creating aggregation reports.
This should be launched with `python -m pious aggregate`
"""

import typer
from typing_extensions import Annotated
from pathlib import Path
import os
import shutil
import textwrap
import tabulate
from ..pio import aggregate
import sys
import time

banner = f"""
Create an aggregation report
"""


def aggregate_cmd(
    cfr_file_or_sim_dir: Annotated[
        Path,
        typer.Argument(
            help="Either a cfr file (for a single file aggregation report) or a directory containing cfr files"
        ),
    ],
    lines: Annotated[list[str], typer.Argument(help="Explicit nodes to add")] = None,
    flop: Annotated[bool, typer.Option(help="Add all flop nodes")] = False,
    turn: Annotated[bool, typer.Option(help="Add all turn nodes")] = False,
    river: Annotated[bool, typer.Option(help="Add all river nodes")] = False,
    out: Annotated[Path, typer.Option(help="Where to write files")] = None,
    print_results: Annotated[
        bool, typer.Option("--print", help="Print results to stdout")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option(help="Overwrite results of a computation")
    ] = False,
    progress: Annotated[bool, typer.Option(help="Print progress bar")] = False,
):
    """Create aggregation reports from CFR files"""
    if lines is None:
        lines = []

    if not cfr_file_or_sim_dir.exists():
        typer.echo(f"No such file or directory {cfr_file_or_sim_dir}", err=True)
        raise typer.Exit(1)

    lines_to_aggregate = aggregate.LinesToAggregate(
        lines=lines,
        flop=flop,
        turn=turn,
        river=river,
    )

    if out is None:
        typer.echo()
        typer.secho("No output directory specified!", fg=typer.colors.RED, err=True)
        typer.echo()
        typer.echo(
            textwrap.fill(
                "Use --out OUTPUT_DIRECTORY to specify where to write the results.",
                width=80,
            )
        )
        raise typer.Exit(1)

    out_dir = out.resolve()
    if out_dir.exists() and not overwrite:
        typer.echo()
        typer.secho("Destination exists!", fg=typer.colors.RED, err=True)
        typer.echo()
        typer.echo(f"    {out_dir}")
        typer.echo()
        typer.echo(
            textwrap.fill(
                f"Use --overwrite to overwrite existing directory, specify a new output directory with --out NEW_DESTINATION, or manually remove destination before rerunning.",
                width=80,
            )
        )
        typer.echo()
        typer.echo("Exiting.", bold=True)
        typer.echo()
        raise typer.Exit(1)

    reports = None
    t0 = time.time()
    if cfr_file_or_sim_dir.is_dir():
        reports = aggregate.aggregate_files_in_dir(
            str(cfr_file_or_sim_dir), lines_to_aggregate, print_progress=progress
        )
        typer.echo(list(reports.keys()))
    elif cfr_file_or_sim_dir.is_file():
        reports = aggregate.aggregate_single_file(
            str(cfr_file_or_sim_dir), lines_to_aggregate, print_progress=progress
        )
    else:
        typer.echo(
            f"{cfr_file_or_sim_dir} is neither a .cfr file or a directory", err=True
        )
        raise typer.Exit(1)

    t1 = time.time()
    typer.echo(f"Aggregation completed in {t1 - t0:.2f} seconds.")

    if print_results:
        for line in reports:
            typer.echo()
            typer.echo(f"----- {line} -----")
            df = reports[line]
            typer.echo(tabulate.tabulate(df, headers=df.keys()))
            typer.echo()

    if out is not None and reports is not None:
        if out_dir.exists():
            if overwrite:
                shutil.rmtree(out_dir)
            else:
                raise RuntimeError(f"Destination exists: {out_dir}")

        typer.echo(f"Creating dir {out_dir}")
        os.makedirs(out_dir)
        for line in reports:
            df = reports[line]
            csv_file_name = out_dir / (
                line.line_str.replace("r:0:", "").replace(":", "_") + ".csv"
            )
            typer.echo(str(csv_file_name))
            df.to_csv(csv_file_name, float_format="%.2f", index=False)


# Legacy argparse compatibility (can be removed after full migration)
from argparse import Namespace, _SubParsersAction


def register_command(sub_parsers: _SubParsersAction):
    parser_agg = sub_parsers.add_parser(
        "aggregate", description="Create aggregation reports"
    )

    parser_agg.set_defaults(function=exec_aggregate_main)
    parser_agg.add_argument(
        "cfr_file_or_sim_dir",
        help="Either a cfr file (for a single file aggregation report) or a directory containing cfr files",
    )
    parser_agg.add_argument("lines", nargs="*", help="Explicit nodes to add")
    parser_agg.add_argument("--flop", action="store_true", help="Add all flop nodes")
    parser_agg.add_argument("--turn", action="store_true", help="Add all turn nodes")
    parser_agg.add_argument("--river", action="store_true", help="Add all river nodes")
    parser_agg.add_argument("--out", type=str, help="Where to write files")
    parser_agg.add_argument(
        "--print", action="store_true", help="Print results to stdout"
    )
    parser_agg.add_argument(
        "--overwrite", action="store_true", help="Overwrite results of a computation"
    )
    parser_agg.add_argument(
        "--progress", action="store_true", help="Print progress bar"
    )


def exec_aggregate_main(args: Namespace):
    # Convert argparse Namespace to Typer call
    from pathlib import Path

    cfr_path = Path(args.cfr_file_or_sim_dir)
    out_path = Path(args.out) if args.out else None

    aggregate_cmd(
        cfr_file_or_sim_dir=cfr_path,
        lines=args.lines,
        flop=args.flop,
        turn=args.turn,
        river=args.river,
        out=out_path,
        print_results=args.print,
        overwrite=args.overwrite,
        progress=args.progress,
    )
