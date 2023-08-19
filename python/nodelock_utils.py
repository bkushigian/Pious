from pio_utils import Line
from pyosolver import PYOSolver, Node
from typing import List
from os import path as osp
import time


def get_strategy_at_node(solver, node):
    children = solver.show_children(node)
    strat = solver.show_strategy(node)
    return children, strat


def is_flop(line: Line) -> bool:
    return line.is_flop()


def is_river(line: Line) -> bool:
    return line.is_river()


def is_facing_bet(line: Line) -> bool:
    return line.is_facing_bet()


def is_oop(line: Line) -> bool:
    return line.is_oop()


def filter_lines(lines: List[Line], filters=None):
    if filters is None:
        filters = [is_flop, is_facing_bet, is_oop]

    def filter(line):
        return all((f(line) for f in filters))

    filtered = []
    for line in lines:
        for f in filters:
            if not f(line):
                print(f"Line {line} failed filter {f}")

    return [line for line in lines if filter(line)]


def lock_overfolds(
    solver: PYOSolver,
    lines: List[Line],
    amount=0.01,
    filters=None,
    max_ev_threshold=0.01,
):
    board = solver.show_node("r:0").board
    solver.set_accuracy(10.0)
    print("Board:", board)
    lines = filter_lines(lines, filters=filters)
    print("filtered lines: ", lines)
    print("Rebuilding forgotten streets...")
    print(solver.rebuild_forgotten_streets())
    print("Rebuilding forgotten streets... done")
    for line in lines:
        node_ids = line.get_node_ids(dead_cards=board)
        for node_id in node_ids:
            lock_overfold(
                solver, node_id, amount=amount, max_ev_threshold=max_ev_threshold
            )

    print("Solving...")
    solver.debug = True
    solver.go()
    t = time.time()
    time.sleep(30)
    solver.stop()
    time.sleep(30)

    filename = osp.abspath("overfolded.cfr")
    print(f"Saving {filename}...")
    solver.dump_tree(filename)
    return filters


def lock_overfold(solver: PYOSolver, node_id: str, amount=0.01, max_ev_threshold=0.01):
    global_freq = solver.calc_global_freq(node_id)
    if global_freq < 0.001:
        # print(f"Skipping Node with low global frequency {global_freq}")
        return
    node: Node = solver.show_node(node_id)
    pos = node.get_position()
    pot = node.pot[2]

    put_into_pot_by_player = node.pot[0] if pos == "OOP" else node.pot[1]
    max_ev_to_fold = max_ev_threshold * pot

    player_range = solver.show_range(pos, node_id)
    combos_in_range = sum(player_range)
    if combos_in_range <= 0.05:
        print("Skipping Node with low combos in range")
        return

    strategy = solver.show_strategy(node_id)
    children_actions = solver.show_children_actions(node_id)
    fold_idx = children_actions.index("f")
    fold_freqs = strategy[fold_idx]

    evs, _ = solver.calc_ev(pos, node_id)
    # evs = [ev for ev in evs]

    sorted_indexed_evs = sorted(
        [
            (i, e + put_into_pot_by_player)
            for (i, e) in enumerate(evs)
            if player_range[i] > 0.0 and fold_freqs[i] < 1.0
        ],
        key=lambda x: x[1],
    )

    folded_combos = sum(a * b for (a, b) in zip(player_range, fold_freqs))
    print("=========================")
    print(node_id)
    print("Global freq:", global_freq)
    print(f"Pot: {node.pot}")
    print(f"Max EV to fold: {max_ev_to_fold}")
    fold_freq = folded_combos / combos_in_range

    target_fold_freq = fold_freq + amount

    if target_fold_freq > 1:
        print("WARNING: target_fold_freq > 1")
        target_fold_freq = 1
    target_num_combos = target_fold_freq * combos_in_range
    num_new_combos_to_fold = target_num_combos - folded_combos
    num_new_combos_to_fold_bkp = num_new_combos_to_fold

    print("Range has", combos_in_range, "combos")
    print(
        f"Fold {folded_combos:.1f} / {combos_in_range:.1f} ({100 * fold_freq:.2f}%) combos"
    )
    print(
        f"Target fold {target_num_combos:.1f} / {combos_in_range:.1f} ({100 * target_fold_freq:.2f}%) combos"
    )
    hand_order = solver.show_hand_order()

    # Now we need to iterate through the combos with lowest ev and add their
    # indices to the following list
    indices_and_amounts_of_combos_to_fold = []
    # How many new combos have we folded?

    for idx, ev in sorted_indexed_evs:
        if num_new_combos_to_fold <= 0:
            break
        if player_range[idx] == 0:
            continue
        num_combos_at_idx = player_range[idx]
        folded_combos_at_idx = fold_freqs[idx] * num_combos_at_idx
        combos_to_fold_at_idx = num_combos_at_idx - folded_combos_at_idx

        if combos_to_fold_at_idx >= num_new_combos_to_fold:
            combos_to_fold_at_idx = num_new_combos_to_fold
        num_new_combos_to_fold -= combos_to_fold_at_idx
        # print(
        #     f"{hand_order[idx]}: ev: \033[32;1m{ev:.2f}\033[0m   pot: \033[32;1m{node.pot}\033[0m"
        # )
        # print(
        #     f"    #combos: {num_combos_at_idx:3.3f}\t  fold_freq: {fold_freqs[idx]:3.3f}\t  folded: {folded_combos_at_idx:.3f}\t  unfolded: {num_combos_at_idx  - folded_combos_at_idx:3.3f}"
        # )
        # print(
        #     f"    #fold:   {combos_to_fold_at_idx:3.3f}\t  reamining: {num_new_combos_to_fold:3.3f}\t  of: {num_new_combos_to_fold_bkp:3.3f}"
        # )
        # if ev >= max_ev_to_fold:
        #     print(
        #         f"Warning: Current hand {hand_order[idx]} has ev {ev} >= max ev to fold {max_ev_to_fold}"
        #     )
        #     break
        indices_and_amounts_of_combos_to_fold.append((idx, combos_to_fold_at_idx))

    for idx, amt in indices_and_amounts_of_combos_to_fold:
        # Remove combos from other actions nd add them to fold
        a = 0.0
        for strat_idx in range(len(strategy)):
            if strat_idx == fold_idx:
                continue
            x = strategy[strat_idx][idx]  # Amount of combos in this action
            if a + x > amt:
                x = amt - a
            strategy[strat_idx][idx] -= x
            strategy[fold_idx][idx] += x
            a += x

    flat_strat = []
    for row in strategy:
        flat_strat.extend(row)
    solver.set_strategy(node_id, flat_strat)
    solver.lock_node(node_id)
