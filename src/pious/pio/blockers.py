"""
A module for computing various blocker effects
"""

from .solver import Node, Solver
from .equity import EquityCalculator
from ..util import CARDS, PIO_HAND_ORDER, get_card_index_array
import numpy as np


def compute_single_card_blocker_effects(solver: Solver, node_id: str | Node):
    """
    Compute blocking effects of each card in the current player's range.
    Here, higher is better and lower is worse.
    """
    board = solver.show_board()

    # We don't care about position other than determining which range we are
    # looking at. The hero's range is the current player to act. So we use the
    # current position only to ensure we have the right player's range
    # associated with hero

    node: Node = solver.show_node(node_id)
    pos = node.get_position()
    board = node.board
    hero_is_oop = pos == "OOP"

    hero_range = solver.show_range("IP", node_id)
    villain_range = solver.show_range("OOP", node_id)

    if hero_is_oop:
        hero_range, villain_range = villain_range, hero_range

    # We now have hero and villain's range correctly assigned.  Since position
    # doesn't matter in equity calculations, so we assume that hero is OOP in
    # the equity calculator

    eqc = EquityCalculator(board, oop_range=hero_range, ip_range=villain_range)

    # Get villain equity information (ip)
    equities, matchups, total = eqc.compute_hand_equities(oop=False)
    equities = np.nan_to_num(equities, 0.0)  # Remove nans
    for combo, e in zip(PIO_HAND_ORDER, equities):
        print(combo, e)

    print(board)
    base_villain_equity2 = sum(equities * matchups) / sum(matchups)

    equity_deltas = {}
    blocked_combos = {}
    histograms = {}

    for c in CARDS:
        indicator_array = get_card_index_array(c, negate=False)
        mask_array = get_card_index_array(c, negate=True)

        # First, compute individual equity deltas for this card
        eqs = equities * mask_array
        mus = matchups * mask_array
        eq = sum(eqs * mus) / sum(mus)
        diff = base_villain_equity2 - eq
        equity_deltas[c] = diff

        # Next, collect the blocked combos and their equities
        blocked_combos[c] = [
            (PIO_HAND_ORDER[idx], equities[idx])
            for (idx, indicator) in enumerate(indicator_array)
            if indicator == 1.0 and matchups[idx] > 0.0
        ]

        # Finally, break the equities of the blocked combos into a histogram
        hist = np.zeros(shape=10, dtype=np.float64)
        total_matchups = sum(matchups)
        for idx, indicator in enumerate(indicator_array):
            if indicator == 0.0 or matchups[idx] == 0.0:
                continue
            e = equities[idx]
            hist_bin = min(int(e * 10), 9)
            hist[hist_bin] = matchups[idx] / total_matchups
        histograms[c] = hist

    return equity_deltas, blocked_combos, histograms
