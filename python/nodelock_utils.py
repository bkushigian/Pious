from pio_utils import Line
from pyosolver import PYOSolver, Node
from typing import List


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


def lock_overfolds(solver: PYOSolver, lines: List[Line], amount=0.01, filters=None):
    board = solver.show_node("r:0").board
    print("Board:", board)
    lines = filter_lines(lines, filters=filters)
    print("filtered lines: ", lines)
    node_ids = [line.get_node_ids(dead_cards=board) for line in lines]
    for line in lines:
        node_ids = line.get_node_ids(dead_cards=board)
        for node_id in node_ids:
            lock_overfold(solver, node_id, amount=amount)

    return filters


def lock_overfold(solver: PYOSolver, node_id: str, amount=0.01):
    print("=========================")
    print(node_id)
    node: Node = solver.show_node(node_id)
    pos = node.get_position()
    range = solver.show_range(pos, node_id)
    combos_in_range = sum(range)

    strategy = solver.show_strategy(node_id)
    children_actions = solver.show_children_actions(node_id)
    fold_idx = children_actions.index("f")
    fold_freqs = strategy[fold_idx]

    evs, _ = solver.calc_ev(pos, node_id)

    sorted_indexed_evs = sorted(
        [(i, e) for (i, e) in enumerate(evs) if range[i] > 0], key=lambda x: x[1]
    )

    folded_combos = sum(a * b for (a, b) in zip(range, fold_freqs))
    fold_freq = folded_combos / combos_in_range

    target_fold_freq = fold_freq + amount

    if target_fold_freq > 1:
        print("WARNING: target_fold_freq > 1")
        target_fold_freq = 1
    target_num_combos = target_fold_freq * combos_in_range
    num_new_combos_to_fold = target_num_combos - folded_combos

    print("Range has", combos_in_range, "combos")
    print(
        f"Fold {folded_combos:.1f} / {combos_in_range:.1f} ({100 * fold_freq:.2f}%) combos"
    )
    print(
        f"Target fold {target_num_combos:.1f} / {combos_in_range:.1f} ({100 * target_fold_freq:.2f}%) combos"
    )
    hand_order = solver.show_hand_order()
    for idx, ev in sorted_indexed_evs:
        print(f"{hand_order[idx]}: {ev:.2f}")

    # Now we need to iterate through the combos with lowest ev and add their
    # indices to the following list
    indices_and_amounts_of_combos_to_fold = []
    # How many new combos have we folded?

    for idx, ev in sorted_indexed_evs:
        if num_new_combos_to_fold <= 0:
            break
        if range[idx] == 0:
            continue
        num_combos_at_idx = range[idx]
        folded_combos_at_idx = fold_freqs[idx] * num_combos_at_idx
        combos_to_fold_at_idx = num_combos_at_idx - folded_combos_at_idx

        if combos_to_fold_at_idx >= num_new_combos_to_fold:
            combos_to_fold_at_idx = num_new_combos_to_fold
        num_new_combos_to_fold -= combos_to_fold_at_idx
        print(f"{hand_order[idx]}: ev: {ev:.2f}")
        print(
            f"    freq: {num_combos_at_idx:.3f}, fold_freq: {fold_freqs[idx]}, folded: {folded_combos_at_idx:.3f} combos"
        )
        print(
            f"    fold {combos_to_fold_at_idx:.3f} combos, {num_new_combos_to_fold:.5f} remaining"
        )
        indices_and_amounts_of_combos_to_fold.append((idx, combos_to_fold_at_idx))
