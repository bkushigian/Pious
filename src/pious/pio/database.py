import os
from os import path as osp
import subprocess
from itertools import permutations
from typing import Optional, Tuple


def board_to_ranks_suits(board) -> Tuple[Tuple[str], Tuple[str]]:
    b = board.replace(" ", "")
    if len(b) % 2 != 0:
        if len(b) % 2 != 0:
            raise RuntimeError(f"Invalid board name: {b}")
    ranks = tuple(b[i] for i in range(0, len(b), 2))
    suits = tuple(b[i + 1] for i in range(0, len(b), 2))
    return ranks, suits


def apply_permutation(suits: Tuple[str], perm: Tuple[str]) -> Tuple[str]:
    perm = {a: b for (a, b) in zip("shcd", perm)}
    return tuple(perm[s] for s in suits)


ALL_SUIT_PERMUTATIONS = list(permutations("shdc"))


def find_isomorphic_board(board_path: str) -> Optional[str]:
    board_path = osp.abspath(board_path)
    board = osp.basename(board_path)[:-4]
    db_loc = osp.dirname(board_path)
    if not osp.exists(db_loc):
        raise ValueError(f"No such database location as {db_loc}")
    if not board_path.endswith(".cfr"):
        raise ValueError(f"Illegal board path {board_path}: must have '.cfr' extension")
    print(db_loc)
    db = CFRDatabase(db_loc)
    try:
        iso_board = db.find_isomorphic_board(board)
        return osp.join(db_loc, f"{iso_board}.cfr")
    except ValueError:
        return None


class CFRDatabase:
    def __init__(self, db_location, pio_viewer_location=None):
        if db_location.endswith(".cfr"):
            db_location = osp.dirname(db_location)
        self.db_location = db_location
        self.pio_viewer_location = pio_viewer_location

        if pio_viewer_location is None:
            self.pio_viewer_location = r"C:\PioSOLVER\PioViewer3.exe"
        self.cfr_file_names = [
            f for f in os.listdir(self.db_location) if f.endswith(".cfr")
        ]
        self.cfr_files = [osp.join(db_location, f) for f in self.cfr_file_names]
        self.boards = [b.split(".")[0] for b in self.cfr_file_names]

        self.ranks_to_boards = {}
        for b in self.boards:
            ranks, suits = board_to_ranks_suits(b)
            self.ranks_to_boards.setdefault(ranks, [])
            self.ranks_to_boards[ranks].append(b)

    def find_isomorphic_board(self, board):
        """
        Look for a board in the database that is isomorphic to the provided flop
        """
        ranks, suits = board_to_ranks_suits(board)
        possible_iso_boards = self.ranks_to_boards.get(ranks, [])
        for b in possible_iso_boards:
            _, s = board_to_ranks_suits(b)
            for perm in ALL_SUIT_PERMUTATIONS:
                if apply_permutation(suits, perm) == s:
                    return b
        raise ValueError(
            f"Could not find isomorphic board to {board} in database at {self.db_location}"
        )

    def open_board_in_pio(self, board, node="r:0"):
        """
        Look for this board in the
        """

        board = self.find_isomorphic_board(board)
        idx = self.boards.index(board)
        board_file_path = self.cfr_files[idx]
        if not osp.exists(board_file_path):
            raise RuntimeError(f"Board {board_file_path} does not exist")
        cmd = [self.pio_viewer_location, board_file_path, "--open-node", node]
        print("Running:", " ".join(cmd))
        subprocess.Popen(cmd)
