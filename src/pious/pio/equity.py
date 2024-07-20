"""
Create an equity calculator by wrapping a PioSOLVER instance
"""

from pious.pio.solver import Solver
from pious.pio.util import make_solver


class EquityCalculator:
    def __init__(self, board: str, oop_range: str, ip_range: str):
        self.solver = make_solver()
