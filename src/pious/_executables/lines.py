"""
This module defines the `pious lines`  subcommand for working with PioSOLVER
lines and nodes.
"""

from argparse import Namespace, _SubParsersAction
from typing import List
from ansi.color import fg, fx
from sys import exit
from os import path as osp

from pious.pio.solver import Solver
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
    all_lines_str = solver.show_all_lines()

    if args.show_all:
        show_all_lines(all_lines_str, solver)
    if args.count:
        all_lines = [Line(line, starting_street=FLOP) for line in all_lines_str]
        count(all_lines, root_node_info)
    if args.valid is not None:
        lines_are_valid(args.valid, all_lines_str)


def count(all_lines: List[Line], root_node_info):

    flop_lines = get_flop_lines(lines=all_lines)
    turn_lines = get_turn_lines(lines=all_lines)
    river_lines = get_river_lines(lines=all_lines)

    print("Board:", root_node_info.board)
    print(f"Found {len(all_lines)} lines")
    print("Total lines per street:")
    print(f"Flop: {len(flop_lines):,}")
    print(f"Turn: {len(turn_lines):,}")
    print(f"River: {len(river_lines):,}")

    nodes_per_line = [
        line.get_node_ids(dead_cards=root_node_info.board) for line in all_lines
    ]
    total_nodes = sum([len(nodes) for nodes in nodes_per_line])
    print(f"Expanded all lines to {total_nodes:,} nodes")


def lines_are_valid(lines_to_check: List[str], all_lines: List[str]):
    for line in lines_to_check:
        line_is_valid(line, all_lines)


def line_is_valid(line: str, all_lines: List[str]):
    line_set = set(all_lines)
    if line in line_set:
        print(f"Line {fg.bold}{fg.green}{line}{fx.reset} is valid")
        return True
    print(f"Line {fx.bold}{fg.red}{line}{fx.reset} is invalid")
    subline = "r:0"
    segments = line.split(":")[2:]

    for segment in segments:
        last_subline = subline
        subline = f"{subline}:{segment}"
        if subline not in line_set:
            # We found the first segment that is not in all_lines
            print(
                f"{fx.bold}{fg.blue}{last_subline}{fx.reset} : {fx.bold}{fg.red}{segment}{fx.reset}"
            )
            subline_width = len(last_subline)
            segment_width = len(segment)
            print(f"{fx.bold}{'─' * subline_width}   {'─' * segment_width}{fx.reset}")

            num_colons = last_subline.count(":") + 1
            valid_extensions = [
                l
                for l in line_set
                if l.startswith(last_subline) and l.count(":") == num_colons
            ]
            print(
                f"Found {len(valid_extensions)} valid children of subline {last_subline}"
            )
            print(valid_extensions)
            valid_children = sorted([e.split(":")[-1] for e in valid_extensions])
            for e in valid_children:
                print("-", e.split(":")[-1])


def show_all_lines(all_lines: List[str], solver: Solver):
    for line in all_lines:
        print(line)


def register_command(sub_parsers: _SubParsersAction):
    parser = sub_parsers.add_parser(
        "lines", description="Utility for working with PioSOLVER lines and nodes"
    )
    parser.set_defaults(function=exec_lines)

    parser.add_argument("solve_file", type=str, help="PioSOLVER save file to load")
    parser.add_argument("--count", action="store_true", help="Print a summary of lines")
    parser.add_argument("--valid", nargs="*", help="Check if line is valid")
    parser.add_argument(
        "--show_all", action="store_true", help="Print all lines in tree"
    )
