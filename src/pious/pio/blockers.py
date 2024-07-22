"""
A module for computing various blocker effects
"""

from .solver import Node, Solver
from .equity import EquityCalculator
from ..util import CARDS


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

    # We now have hero and villain's range correctly assigned.  Sine position
    # doesn't matter in equity calculations, so we assume that hero is OOP in
    # the equity calculator

    eqc = EquityCalculator(board, oop_range=hero_range, ip_range=villain_range)

    base_villain_equity = eqc.ip()
    blocker_effects = {}

    for c in CARDS:
        vr = villain_range - c
        eqc.set_ip_range(vr)
        eq = eqc.ip()
        diff = base_villain_equity - eq
        blocker_effects[c] = diff
    return blocker_effects
