from typing import List, Set, Tuple
from argparse import ArgumentParser, Namespace
import time
import sys
from os import path as osp

from pious.pio.line import Line, node_id_to_line
from pious.script_builder import ScriptBuilder
from pious.pio import utils as pio_utils
from pious.pio import nodelock_utils


path = osp.join(osp.dirname(__file__), "..", "resources", "trees", "Ks7h2c.cfr")


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--path", "-p", type=str, default=path)
    parser.add_argument("--log_file", "-l", type=str, default=None)
    parser.add_argument("--debug", "-d", action="store_true")
    parser.add_argument("--store_script", "-s", action="store_true")
    parser.add_argument("--unlock_parent_nodes", action="store_true")
    parser.add_argument("--lock_future_nodes", action="store_true")
    parser.add_argument("--overfold_amount", "-A", type=float, default=0.05)
    parser.add_argument("--disable_script_optimization", action="store_true")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="where to write to file (default is change 'X.cfr' to 'X_overfolded.cfr' to the end of the original filename)",
    )
    parser.add_argument(
        "--save_type", default="small", help="normal, small, or very_small"
    )
    parser.add_argument(
        "--accuracy",
        default=0.05,
        type=float,
        help="accuracy, as percent of pot",
    )
    # Filters
    parser.add_argument("--flop", action="store_true")
    parser.add_argument("--turn", action="store_true")
    parser.add_argument("--river", action="store_true")
    parser.add_argument("--oop", action="store_true")
    parser.add_argument("--ip", action="store_true")
    parser.add_argument("--num_bets", type=int, default=3)
    parser.add_argument("--bets_per_street", type=int, default=1)

    return parser.parse_args()


def create_filters_fns(
    flop=False,
    turn=False,
    river=False,
    oop=False,
    ip=False,
    num_bets=None,
    bets_per_street=None,
):
    # Build filters

    street_filters = []
    if flop:
        street_filters.append(pio_utils.is_flop)

    if turn:
        street_filters.append(pio_utils.is_turn)

    if river:
        street_filters.append(pio_utils.is_river)

    def street_filter(line: Line):
        for f in street_filters:
            if f(line):
                return True
        return False

    position_filters = []
    if ip:
        position_filters.append(pio_utils.is_ip)
    if oop:
        position_filters.append(pio_utils.is_oop)

    def position_filter(line: Line):
        for f in position_filters:
            if f(line):
                return True
        return False

    bet_filters = []

    if num_bets is not None:
        bet_filters.append(lambda line: pio_utils.num_bets(line) <= num_bets)
    if bets_per_street is not None:
        bet_filters.append(
            lambda line: max(pio_utils.bets_per_street(line)) <= bets_per_street
        )

    def bet_filter(line: Line):
        for f in bet_filters:
            if not f(line):
                return False
        return True

    return street_filter, position_filter, bet_filter, pio_utils.is_facing_bet


def filter_lines_and_expand_to_node_ids(
    lines, board, filters
) -> Tuple[List[Line], List[str]]:
    filtered_lines = pio_utils.filter_lines(lines=lines, filters=filters)
    print(f"Filtered {len(lines):,} lines down to {len(filtered_lines):,} lines")

    node_ids = []
    for line in filtered_lines:
        node_ids += line.get_node_ids(dead_cards=board)
    print(f"Expanded {len(filtered_lines):,} lines to {len(node_ids):,} nodes")
    return filtered_lines, node_ids


def main():
    args = parse_args()

    if args.ip and args.oop:
        print("Error: both --ip and --oop are set")
        sys.exit(1)

    solver = pio_utils.make_solver(
        debug=args.debug, log_file=args.log_file, store_script=args.store_script
    )
    path = osp.abspath(args.path)
    solver.load_tree(f'"{path}"')

    root_node_info = solver.show_node("r:0")
    board = root_node_info.board
    pot = root_node_info.pot[2]
    print("pot =", pot)

    all_lines = [
        Line(line, starting_street=pio_utils.FLOP) for line in solver.show_all_lines()
    ]
    filters = create_filters_fns(
        flop=args.flop,
        turn=args.turn,
        river=args.river,
        oop=args.oop,
        ip=args.ip,
        num_bets=args.num_bets,
        bets_per_street=args.bets_per_street,
    )
    filtered_lines, node_ids = filter_lines_and_expand_to_node_ids(
        lines=all_lines, filters=filters, board=board
    )

    print("Rebuilding forgotten streets...", end="", flush=True)
    solver.rebuild_forgotten_streets()
    print("DONE")

    if args.disable_script_optimization:
        script_builder = None
    else:
        script_builder = ScriptBuilder()
    print("Locking overfolds...")
    t0 = time.time()
    locked_node_ids = nodelock_utils.lock_overfolds(
        solver,
        node_ids,
        overfold_amount=args.overfold_amount,
        script_builder=script_builder,
    )
    t1 = time.time()
    print(f"Finished in {t1-t0:1f} seconds")

    if not args.unlock_parent_nodes:
        # Now, add all parent nodes to be locked to ensure that the solver
        # can't adjust its strategy on previous streets to avoid being
        # exploited

        # To do this we:
        # 1. Get all the lines associated with the locked nodes
        # 2. Get all the ancestor nodes of those lines that belong
        #    to the locked player
        # 3. Expand those to all nodes
        # 4. Lock those nodes

        # This is not quite correct, but it's good enough for now. The correct
        # way to do this would be to use a trie and store all nodes in the trie.
        # then we could traverse the trie backwards

        # We use a set to deduplicate

        locker = solver
        if script_builder is not None:
            locker = script_builder

        lines_of_locked_nodes: Set[Line] = set()
        for node_id in locked_node_ids:
            lines_of_locked_nodes.add(node_id_to_line(node_id))

        print("Gathering parent nodes...")
        parent_lines = set()
        for line in lines_of_locked_nodes:
            p = line.get_current_player_previous_action()
            while p is not None:
                parent_lines.add(p)
                p = p.get_current_player_previous_action()

        parent_node_ids = []
        for line in parent_lines:
            parent_node_ids += line.get_node_ids(dead_cards=board)

        num_node_ids = len(parent_node_ids)

        t0 = time.time()
        print(f"Locking {len(parent_node_ids):,} parent nodes")
        for i, node_id in enumerate(parent_node_ids):
            if node_id not in locked_node_ids:
                locker.lock_node(node_id)
            if (i + 1) % 100 == 0:
                print(
                    f"\r{i+1}/{num_node_ids} ({100.0 * (i+1)/num_node_ids:.1f}%)",
                    end="",
                )
        print(f"\r{num_node_ids}/{num_node_ids} (100.0%)")

        if script_builder is not None:
            print("Writing and running locking scripts...")
            script_builder.write_script(osp.abspath("locking_script.txt"))
            t2 = time.time()
            solver.load_script_silent(osp.abspath("locking_script.txt"))
            t3 = time.time()
            print(f"Ran script in {t3-t2:.1f} seconds")
        t1 = time.time()
        print(f"Finished locking parent nodes in {t1-t0:.1f} seconds")
    # Now, solve!
    print("Solving...")
    print(
        f"Accuracy (in chips): {args.accuracy:.3f}% ({(args.accuracy / 100) * pot:.3f})"
    )
    solver.set_accuracy(args.accuracy * pot, "chips")
    solver.go()
    output = args.output
    if output is None:
        output = args.path.strip(".cfr") + "_overfolded.cfr"
    output = osp.abspath(output)
    print("Saving tree to", output)
    solver.dump_tree(filename=output, save_type=args.save_type)


if __name__ == "__main__":
    main()
