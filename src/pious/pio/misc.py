from pious.pio import Solver, Node
import numpy as np

from pious.util import PIO_HAND_ORDER


def calc_ev_deltas(
    solver: Solver, player: str, before_node: str | Node, after_node: str | Node
):
    evs1, mus1 = solver.calc_ev(player, before_node)
    evs2, mus2 = solver.calc_ev(player, after_node)

    deltas = evs2 - evs1
    return deltas


def find_mix_call_folds(solver: Solver, node: str | Node):
    """
    return (idx, hand, call_freq, fold_freq) for every mix call/fold
    """
    actions = solver.show_children_actions(node)
    if "c" in actions and "f" in actions:
        strats = solver.show_strategy(node)
        c_idx = actions.index("c")
        f_idx = actions.index("f")
        calls = strats[c_idx]
        folds = strats[f_idx]
        return [
            (i, h, c, f)
            for (i, (h, c, f)) in enumerate(zip(solver.show_hand_order(), calls, folds))
            if c > 0 and f > 0
        ]
    return []


def set_hands_to_pure_fold(solver: Solver, node: str | Node, indices):
    print(solver.load_all_nodes())
    print(solver.rebuild_forgotten_streets())
    actions = solver.show_children_actions(node)
    if "f" in actions:
        f_idx = actions.index("f")
        strat = solver.show_strategy(node)
        updated_indices = []
        for a_idx in range(len(strat)):
            for h_idx in indices:
                updated_indices.append((a_idx, h_idx))
                v1 = strat[a_idx][h_idx]
                if a_idx == f_idx:
                    strat[a_idx][h_idx] = 1.0
                    v2 = strat[a_idx][h_idx]
                else:
                    strat[a_idx][h_idx] = 0.0
                    v2 = strat[a_idx][h_idx]
                print(f"Updating strat[{a_idx}][{h_idx}] {v1} -> {v2}")
        new_strat = np.concatenate(strat)
        print("Found new strat")
        orig_strat = solver.show_strategy(node)
        print(solver.set_strategy(node, new_strat))
        updated_strat = solver.show_strategy(node)
        print("Updated?", orig_strat != updated_strat)
        solver.calc_results()
        pass


def experiment():
    from pious.pio import make_solver

    tree = r"F:\Database\SimpleTree\SRP\b25\BTNvBB\Jd5c2c.cfr"
    node_cbet = "r:0:c"
    node_cbet_response = "r:0:c:b12"
    s = make_solver()
    s.load_tree(tree)
    evs0 = s.calc_ev("IP", node_cbet)[0]  # Before resetting strategy
    mixes = find_mix_call_folds(s, node_cbet_response)
    indices = [e[0] for e in mixes]
    set_hands_to_pure_fold(s, node_cbet_response, indices)
    evs1 = s.calc_ev("IP", node_cbet)[0]
    deltas = evs1 - evs0
    deltas = np.nan_to_num(deltas, posinf=0.0, neginf=0.0)
    hand_deltas = sorted(list(zip(PIO_HAND_ORDER, deltas)), key=lambda x: x[1])
    for h, d in hand_deltas:
        print(f"{h}: {d:6.2f}")
    return deltas
