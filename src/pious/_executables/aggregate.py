"""
This module implements an executable interface for creating aggregation reports.
This should be launched with `python -m pious aggregate`
"""

from argparse import Namespace, _SubParsersAction
from os import path as osp
import os
import shutil
import tabulate
from ..pio import aggregate


banner = f"""
Create an aggregation report
"""


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


def exec_aggregate_main(args: Namespace):
    if not osp.exists(args.cfr_file_or_sim_dir):
        print(f"No such file or directory {args.cfr_file_or_sim_dir}")
        exit(-1)

    lines = aggregate.LinesToAggregate(
        lines=args.lines,
        flop=args.flop,
        turn=args.turn,
        river=args.river,
    )

    reports = None
    if osp.isdir(args.cfr_file_or_sim_dir):
        reports = aggregate.aggregate_files_in_dir(args.cfr_file_or_sim_dir, lines)
        print(reports.keys())
    elif osp.isfile(args.cfr_file_or_sim_dir):
        reports = aggregate.aggregate_single_file(args.cfr_file_or_sim_dir, lines)
        pass
    else:
        print(f"{args.cfr_file_or_sim_dir} is neither a .cfr file or a directory")
        exit(-1)

    if args.print:
        for line in reports:
            print()
            print(f"----- {line} -----")
            df = reports[line]
            print(tabulate.tabulate(df, headers=df.keys()))
            print()
    if args.out is not None and reports is not None:
        out_dir = osp.abspath(args.out)
        if osp.exists(out_dir):
            if args.overwrite:
                shutil.rmtree(out_dir)
            else:
                raise RuntimeError(f"Destination exists: {out_dir}")

        print("Creating dir", out_dir)
        os.makedirs(out_dir)
        for line in reports:
            df = reports[line]
            csv_file_name = (
                osp.join(out_dir, line.line_str.replace("r:0:", "").replace(":", "_"))
                + ".csv"
            )
            print(csv_file_name)
            df.to_csv(csv_file_name, float_format="%.2f", index=False)
