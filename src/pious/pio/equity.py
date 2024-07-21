"""
Create an equity calculator by wrapping a PioSOLVER instance
"""

from pious.pio.solver import Solver
from pious.pio.util import make_solver
from pious.range import Range
import numpy as np


class EquityCalculator:
    def __init__(self, board: str, oop_range: str | Range, ip_range: str | Range):
        self.solver: Solver = make_solver()
        self.oop_range = Range(oop_range)
        self.ip_range = Range(ip_range)
        self.board = None

        self.solver.set_eff_stack(100)
        self.solver.set_pot(0, 0, 100)
        self.solver.set_isomorphism(1, 0)
        self.solver.clear_lines()

        self.set_board(board)

        self.solver.set_range("OOP", self.oop_range.pio_str())
        self.solver.set_range("IP", self.ip_range.pio_str())
        self.solver.build_tree()

    @staticmethod
    def sanitize_board(b):
        return "".join([c for c in b if c not in " \n\t,"])

    def compute_equity(self, oop=True, preflop=False):
        if oop:
            pos = "OOP"
        else:
            pos = "IP"

        if preflop:
            _, _, total = self.solver.calc_eq_preflop(pos)
        else:
            _, _, total = self.solver.calc_eq_node(pos, "r:0")
        return total

    def set_board(self, board):
        self.board = EquityCalculator.sanitize_board(board)
        b = self.board
        if len(b) % 2 != 0:
            raise ValueError(f"Illegal board: {b}")
        self.solver.set_board(b)
        self._add_lines()
        self.solver.build_tree()

    def _add_lines(self):
        self.solver.clear_lines()
        b = self.board
        self.solver.set_board(b)

        n_cards = len(b) // 2
        if n_cards == 3:  # Flop
            self.solver.add_line("0 0 0 0 0 0")
        elif n_cards == 4:  # Turn
            self.solver.add_line("0 0 0 0")
        elif n_cards == 5:  # River
            self.solver.add_line("0 0")

    def set_oop_range(self, r):
        self.oop_range = Range(r)
        self.solver.set_range("OOP", self.oop_range.pio_str())
        self.solver.build_tree()

    def set_ip_range(self, r):
        self.oop_range = Range(r)
        self.solver.set_range("IP", self.oop_range.pio_str())
        self.solver.build_tree()

    def oop(self, preflop=False):
        return self.compute_equity(oop=True, preflop=preflop)

    def ip(self, preflop=False):
        return self.compute_equity(oop=False, preflop=preflop)

    def clear_board(self):
        self.solver.set_board("")
        self.solver.build_tree()
