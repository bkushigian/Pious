"""
This module defines the `pious lines`  subcommand for working with PioSOLVER
lines and nodes.
"""

from argparse import Namespace, _SubParsersAction
from ansi.color import fg, fx
from pkg_resources import resource_filename
from sys import exit
import time
from os import path as osp
from ..pio import (
    make_solver,
    Line,
    get_flop_lines,
    get_turn_lines,
    get_river_lines,
)

FLOP = 1


def exec_lines(args: Namespace):

    if not osp.exists(args.solve_file):
        print(f"No such file {args.solve_file}, exiting")
        exit(-1)

    solve_file = osp.abspath(args.solve_file)

    solver = make_solver()
    solver.load_tree(solve_file)
    solver.load_all_nodes()

    root_node_info = solver.show_node("r:0")
    all_lines = solver.show_all_lines()
    all_lines = [Line(line, starting_street=FLOP) for line in solver.show_all_lines()]

    print("Board:", root_node_info.board)
    print(f"Found {len(all_lines)} lines")

    flop_lines = get_flop_lines(lines=all_lines)
    turn_lines = get_turn_lines(lines=all_lines)
    river_lines = get_river_lines(lines=all_lines)

    print("Total lines per street:")
    print(f"Flop: {len(flop_lines)}")
    print(f"Turn: {len(turn_lines)}")
    print(f"River: {len(river_lines)}")

    print("Expanding all lines to nodes...")
    t_0 = time.time()
    nodes_per_line = [
        line.get_node_ids(dead_cards=root_node_info.board) for line in all_lines
    ]

    total_nodes = sum([len(nodes) for nodes in nodes_per_line])

    print(f"Expanded all lines to {total_nodes} nodes")


def register_command(sub_parsers: _SubParsersAction):
    parser = sub_parsers.add_parser(
        "lines", description="Utility for working with PioSOLVER lines and nodes"
    )
    parser.set_defaults(function=exec_lines)

    parser.add_argument("solve_file", type=str, help="PioSOLVER save file to load")
