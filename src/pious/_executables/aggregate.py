"""
This module implements an executable interface for creating aggregation reports.
This should be launched with `python -m pious aggregate`
"""

from argparse import Namespace, _SubParsersAction
from os import path as osp
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


def exec_aggregate_main(args: Namespace):
    if not osp.exists(args.cfr_file_or_sim_dir):
        print(f"No such file or directory {args.cfr_file_or_sim_dir}")
        exit(-1)

    if osp.isdir(args.cfr_file_or_sim_dir):
        pass
    elif osp.isfile(args.cfr_file_or_sim_dir):
        reports = aggregate.aggregate_single_file(
            args.cfr_file_or_sim_dir,
            aggregate.LinesToAggregate(
                lines=args.lines,
                flop=args.flop,
                turn=args.turn,
                river=args.river,
            ),
        )
        for line in reports:
            print(line)
            df = reports[line]
            print(tabulate.tabulate(df, headers=df.keys()))
        pass
    else:
        print(f"{args.cfr_file_or_sim_dir} is neither a .cfr file or a directory")
        exit(-1)
