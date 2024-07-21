"""
A module for computing various blocker effects
"""

from pious.pio.solver import Node, Solver


def compute_blocker(solver: Solver, node_id: str | Node):
    """
    Compute blocking effects of each card in the current player's range.
    """
    oop = solver.show_range("OOP", node_id)
    ip = solver.show_range("IP", node_id)
