from pio_utils import Line
from pyosolver import PYOSolver
from typing import List


def lock_overfolds(solver, all_lines: List[Line], amount=0.01, filters=None):
    if filters is None:
        filters = [
            lambda line: line.is_river() and line.is_oop() and line.is_facing_bet()
        ]

    return filters
