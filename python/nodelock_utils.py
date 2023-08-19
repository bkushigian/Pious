from pio_utils import Line, filter_lines
from pyosolver import PYOSolver, Node
from typing import List
from os import path as osp
import time


def get_strategy_at_node(solver, node):
    children = solver.show_children(node)
    strat = solver.show_strategy(node)
    return children, strat


def lock_overfolds(
    solver: PYOSolver,
    node_ids: List[str],
    amount=0.05,
    max_ev_threshold=0.05,
) -> List[str]:
    solver.set_accuracy(10.0)

    locked_node_ids = []

    num_node_ids = len(node_ids)
    for i, node_id in enumerate(node_ids):
        if lock_overfold_at_node_id(
            solver,
            node_id,
            amount=amount,
            max_ev_threshold=max_ev_threshold,
            min_global_freq=0.000001,
        ):
            locked_node_ids.append(node_id)
        if (i + 1) % 100 == 0:
            print(f"\r{i+1}/{num_node_ids}", end="")
        print()

    return node_ids


def lock_overfold_at_node_id(
    solver: PYOSolver,
    node_id: str,
    amount=0.01,
    max_ev_threshold=0.01,
    min_global_freq=0.001,
) -> bool:
    """
    Lock a given node to overfold by specified amount. Return `True` if the lock
    succeeds (i.e., the node occurs enough) and `False` otherwise.
    """
    node: Node = solver.show_node(node_id)
    if node is None:
        return False
    global_freq = solver.calc_global_freq(node_id)
    if global_freq < min_global_freq:
        return False
    pos = node.get_position()
    if pos is None:
        return False
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
    if "f" not in children_actions:
        return False
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
    # print("=========================")
    # print(node_id)
    # print("Global freq:", global_freq)
    # print(f"Pot: {node.pot}")
    # print(f"Max EV to fold: {max_ev_to_fold}")
    fold_freq = folded_combos / combos_in_range

    target_fold_freq = fold_freq + amount

    if target_fold_freq > 1:
        # print("WARNING: target_fold_freq > 1")
        target_fold_freq = 1
    target_num_combos = target_fold_freq * combos_in_range
    num_new_combos_to_fold = target_num_combos - folded_combos

    # print("Range has", combos_in_range, "combos")
    # print(
    #     f"Fold {folded_combos:.1f} / {combos_in_range:.1f} ({100 * fold_freq:.2f}%) combos"
    # )
    # print(
    #     f"Target fold {target_num_combos:.1f} / {combos_in_range:.1f} ({100 * target_fold_freq:.2f}%) combos"
    # )
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

    return True
