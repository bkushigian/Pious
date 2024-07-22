"""
A module for computing various blocker effects
"""

from .solver import Node, Solver
from .equity import EquityCalculator
from ..util import CARDS, get_card_index_array
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

    pos = solver.show_node(node_id).get_position()
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

    base_villain_equity = eqc.ip()
    base_villain_equity2 = sum(equities * matchups) / sum(matchups)

    print(base_villain_equity, base_villain_equity2)

    blocker_effects = {}

    for c in CARDS:
        a = get_card_index_array(c, negate=True)
        eqs = equities * a
        mus = matchups * a
        eq = sum(eqs * mus) / sum(mus)
        diff = base_villain_equity - eq
        blocker_effects[c] = diff
    return blocker_effects
