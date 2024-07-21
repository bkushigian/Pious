"""
Create an equity calculator by wrapping a PioSOLVER instance
"""

from typing import List, Sequence, Tuple
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

        self.solver.set_range("OOP", self.oop_range)
        self.solver.set_range("IP", self.ip_range)
        self.solver.build_tree()

    @staticmethod
    def sanitize_board(b):
        return "".join([c for c in b if c not in " \n\t,"])

    def compute_equity(self, oop: bool = True, preflop: bool = False):
        if oop:
            pos = "OOP"
        else:
            pos = "IP"

        if preflop:
            _, _, total = self.solver.calc_eq_preflop(pos)
        else:
            _, _, total = self.solver.calc_eq_node(pos, "r:0")
        return total

    def compute_equities(self, preflop: bool = False) -> Tuple[float, float]:
        """
        Compute oop and ip equities.
        """
        oop = self.compute_equity(oop=True, preflop=preflop)
        ip = self.compute_equity(oop=False, preflop=preflop)
        return oop, ip

    def set_board(self, board: Sequence[str] | str):
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


def sanitize_board(board: str | Sequence[str]):
    """
    Sanitize a board to either
    """
    b = board
    if isinstance(board, Sequence):
        b = "".join([c.strip() for c in board])
    if not isinstance(b, str):
        raise ValueError(
            f"Invalid board {board}: must be a sequence of cards or a string"
        )
    return b


def compute_equities(
    board: str | Sequence[str],
    oop_range: str | Range,
    ip_range: str | Range,
    preflop: bool = False,
) -> Tuple[float, float]:
    """
    Compute OOP and IP equities on a board given specified ranges.
    """
    # First, sanitize board to a string
    b = sanitize_board(board)
    return EquityCalculator(b, oop_range, ip_range).compute_equities(preflop=preflop)
