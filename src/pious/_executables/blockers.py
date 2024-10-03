from argparse import Namespace, _SubParsersAction
from ..pio import compute_single_card_blocker_effects, make_solver
from os import path as osp
from sys import exit


def exec_blockers(args: Namespace):
    solve_path = args.solve_file
    node_id = args.node_id
    num_hist_bins = args.num_hist_bins
    if node_id is None:
        node_id = "r:0"
    if not node_id.startswith("r:0"):
        node_id = "r:0" + node_id
    if not osp.exists(solve_path):
        print(f"No such file {solve_path}, exiting")
        exit(-1)
    solver = make_solver()
    solver.load_tree(solve_path)
    blocker_effects = compute_single_card_blocker_effects(
        solver, node_id, num_hist_bins
    )

    if not args.no_graph:
        blocker_effects.print_graph(print_suits=not args.no_graph_suits)
    if args.per_card or args.cards_to_print is not None:
        blocker_effects.print_per_card(cards_to_print=args.cards_to_print)
    if args.grid:
        blocker_effects.print_grid()


def register_command(sub_parsers: _SubParsersAction):
    parser_blocker = sub_parsers.add_parser(
        "blockers", description="Compute and show blocker effects"
    )
    parser_blocker.set_defaults(function=exec_blockers)
    parser_blocker.add_argument("solve_file", help="Pio solve to load")
    parser_blocker.add_argument("node_id", help="Node to inspect (e.g., 'r:0:x:b12')")
    parser_blocker.add_argument(
        "--num_hist_bins",
        type=int,
        default=10,
        help="Number of histogram bins to display",
    )
    parser_blocker.add_argument(
        "--per_card", action="store_true", help="Print per-card detailed data"
    )
    parser_blocker.add_argument(
        "--grid", action="store_true", help="Print grid of blocker effects"
    )
    parser_blocker.add_argument(
        "--no_graph_suits",
        action="store_true",
        help="Don't print suits in graph (makes graph narrower but less legible)",
    )
    parser_blocker.add_argument(
        "--cards_to_print",
        type=str,
        help="Cards to print for detailed information (automatically toggles --per_card)",
    )
    parser_blocker.add_argument(
        "--no_graph", action="store_true", help="Do not print graph"
    )
