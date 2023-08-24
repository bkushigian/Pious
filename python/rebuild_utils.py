""" 
Rebuild Utility Functions

This module contains utility functions to rebuild and resolve a game tree.
This is to replace the broken functionality of `solve_all_spots` from UPI
"""

from argparse import ArgumentParser
from pyosolver import PYOSolver, Node
from pio_utils import Line, filter_lines, is_flop, is_turn, is_nonterminal
from progress_bar import progress_bar
from pio_utils import make_solver, FLOP, TURN
from os import path as osp
import time


def rebuild_and_resolve(solver: PYOSolver, lock_turns=True, lines=None, accuracy=0.05):
    """
    Rebuild and resolve a game tree. This is to replace the broken functionality
    of `solve_all_spots` from UPI.

    Parameters
    ----------
    solver : PYOSolver
        The solver to use for rebuilding and resolving.
    lock_turns : bool, optional
        Whether to lock turns or not, by default True
    lines : list, optional
        The lines to use for rebuilding and resolving. If None, then all lines
        will be used, by default None
    accuracy : float, optional
        The accuracy as percent of pot to use for resolving, by default 0.05
    """
    if not solver.is_ready():
        return False

    effective_stack = solver.show_effective_stack()
    root_node = solver.show_node("r:0")
    board = root_node.board

    pot = root_node.pot[2]
    print(f"pot = {pot}")
    accuracy_in_chips = accuracy * pot
    print(f"accuracy = {accuracy_in_chips}")
    solver.set_accuracy(accuracy_in_chips)

    print(solver.estimate_rebuild_forgotten_streets())
    print("Rebuilding forgotten streets...", end="", flush=True)
    t0 = time.time()
    solver.rebuild_forgotten_streets()
    t1 = time.time()
    print("DONE")
    print(f"Rebuilt forgotten streets in {t1 - t0:3.2f} seconds")

    if lines is None:
        print("Collecting all lines...", end="", flush=True)
        lines = solver.show_all_lines()
        print("DONE")

    print(f"Collected {len(lines):,} lines")
    lines = [
        Line(line, starting_street=FLOP, effective_stack=effective_stack)
        for line in lines
        if len(line) > 2
    ]

    # Apply filters
    filters = [is_nonterminal]

    if lock_turns:
        filters.append(lambda line: is_flop(line) or is_turn(line))
    else:
        filters.append(is_flop)
    filtered_lines = filter_lines(lines, filters)

    print(f"Filtered {len(lines):,} lines down to {len(filtered_lines):,} lines")

    node_ids = []
    for line in filtered_lines:
        node_ids += line.get_node_ids(dead_cards=board)

    print(f"Expanded {len(filtered_lines):,} lines to {len(node_ids):,} nodes")

    t0 = time.time()
    for node_id in progress_bar(node_ids, prefix="Locking nodes"):
        solver.lock_node(node_id)
    t1 = time.time()
    print(f"Locked nodes in {t1 - t0:3.2f} seconds")

    print("Resolving full tree...", end="", flush=True)
    t0 = time.time()
    solver.go()
    t1 = time.time()
    print("DONE")
    print(f"Resolved full tree in {t1 - t0:3.2f} seconds")


def main():
    parser = ArgumentParser()
    parser.add_argument("path", type=str, help="CFR file to rebuild")
    parser.add_argument("--output", type=str, help="Output file")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    parser.add_argument("--lock_turns", action="store_true", help="Lock turns")
    parser.add_argument(
        "--accuracy", type=float, default=0.05, help="Set accuracy as percent of pot"
    )

    args = parser.parse_args()
    in_path = f'"{osp.abspath(args.path)}"'
    solver = make_solver(debug=args.debug)
    print(f"Loading tree from {in_path}...", end="", flush=True)
    t0 = time.time()
    solver.load_tree(f"{in_path}")
    t1 = time.time()
    print("DONE")
    print(f"Loaded tree in {t1 - t0:3.2f} seconds")

    t0 = time.time()
    rebuild_and_resolve(solver, lock_turns=args.lock_turns, accuracy=args.accuracy)
    t1 = time.time()
    print(f"Rebuilt and resolved tree in {t1 - t0:3.2f} seconds")


if __name__ == "__main__":
    print("WARNING: This is for testing only")
    main()
