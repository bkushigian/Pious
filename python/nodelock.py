from typing import List, Tuple
import pio_utils
import nodelock_utils
import pyosolver
from argparse import ArgumentParser
import time
import sys

from os import path as osp

path = osp.join(osp.dirname(__file__), "..", "resources", "trees", "Ks7h2c.cfr")


def create_filters_fns(flop=False, turn=False, river=False, oop=False, ip=False):
    # Build filters
    street_filters = []
    if flop:
        street_filters.append(pio_utils.is_flop)

    if turn:
        street_filters.append(pio_utils.is_turn)

    if river:
        street_filters.append(pio_utils.is_river)

    def street_filter(line: pio_utils.Line):
        for f in street_filters:
            if f(line):
                return True
        return False

    position_filters = []
    if ip:
        position_filters.append(pio_utils.is_ip)
    if oop:
        position_filters.append(pio_utils.is_oop)

    def position_filter(line: pio_utils.Line):
        for f in position_filters:
            if f(line):
                return True
        return False

    return street_filter, position_filter, pio_utils.is_facing_bet


def filter_lines_and_expand_to_node_ids(
    lines, board, filters
) -> Tuple[List[pio_utils.Line], List[str]]:
    filtered_lines = pio_utils.filter_lines(lines=lines, filters=filters)
    print(f"Filtered {len(lines):,} down to {len(filtered_lines):,}")

    node_ids = []
    for line in filtered_lines:
        node_ids += line.get_node_ids(dead_cards=board)
    print(f"Expanded {len(filtered_lines):,} lines to {len(node_ids):,} nodes")
    return filtered_lines, node_ids


def main():
    parser = ArgumentParser()
    parser.add_argument("--path", "-p", type=str, default=path)
    parser.add_argument("--log_file", "-l", type=str, default=None)
    parser.add_argument("--debug", "-d", action="store_true")
    parser.add_argument("--store_script", "-s", action="store_true")
    parser.add_argument("--unlock_parent_nodes", action="store_true")
    parser.add_argument("--lock_future_nodes", action="store_true")
    parser.add_argument(
        "--save_type", default="small", help="normal, small, or very_small"
    )
    # Filters
    parser.add_argument("--flop", action="store_true")
    parser.add_argument("--turn", action="store_true")
    parser.add_argument("--river", action="store_true")
    parser.add_argument("--oop", action="store_true")
    parser.add_argument("--ip", action="store_true")
    # parser.add_argument(
    #     "--global_frequency",
    #     type=float,
    #     defualt=None,
    #     help="minimum global frequency of a node needed to lock",
    # )

    args = parser.parse_args()

    if args.ip and args.oop:
        print("Error: both --ip and --oop are set")
        sys.exit(1)

    solver = pio_utils.make_solver(
        debug=args.debug, log_file=args.log_file, store_script=args.store_script
    )
    solver.load_tree(f'"{args.path}"')

    root_node_info = solver.show_node("r:0")
    board = root_node_info.board

    all_lines = [
        pio_utils.Line(line, starting_street=pio_utils.FLOP)
        for line in solver.show_all_lines()
    ]
    filters = create_filters_fns(
        flop=args.flop, turn=args.turn, river=args.river, oop=args.oop, ip=args.ip
    )
    filtered_lines, node_ids = filter_lines_and_expand_to_node_ids(
        lines=all_lines, filters=filters, board=board
    )

    print("Rebuilding forgotten streets...", end="")
    solver.rebuild_forgotten_streets()
    print("DONE")

    print("Locking overfolds...")
    t = time.time()
    locked_node_ids = nodelock_utils.lock_overfolds(solver, node_ids, amount=0.05)
    t = time.time() - t
    print(f"Finished in {t} seconds")

    if not args.unlock_parent_nodes:
        # Now, add all parent nodes to be locked
        parent_nodes = set()
        for node_id in locked_node_ids:
            actions = node_id.split(":")[2:]  # Strip root
            while actions:
                popped_actions = 0
                while popped_actions < 2:
                    a = actions.pop()
                    if a not in pio_utils.CARDS:
                        popped_actions += 1
                parent_nodes.add

        pass


if __name__ == "__main__":
    main()
