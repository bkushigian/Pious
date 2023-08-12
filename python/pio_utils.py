"""
A collection of utility functions
"""

from typing import List, Tuple
from pyosolver import PYOSolver

CARDS = tuple(f"{r}{s}" for r in "23456789TJQKA" for s in "shdc")
PATH = r"C:\\PioSOLVER"
EXECUTABLE = r"PioSOLVER2-edge"


class Line:
    def __init__(self, line: str):
        self.line = line
        self.root, self.streets = line_to_streets(line)
        self.actions = line.split(":")
        self.nodes = {}

    def get_nodes(self, dead_cards=None):
        """
        Get the nodes associated with this line. If the nodes have not been
        computed, compute them.
        """

        if dead_cards is None:
            dead_cards = []
        # Make dead cards hashable
        dead_cards = tuple(sorted(dead_cards))
        if dead_cards not in self.nodes:
            self.nodes[dead_cards] = lines_to_nodes([self.line], dead_cards=dead_cards)
        return self.nodes[dead_cards]


def make_solver(
    install_path=PATH,
    executable=EXECUTABLE,
    debug=False,
    log_file=None,
    store_script=False,
) -> PYOSolver:
    return PYOSolver(
        install_path,
        executable,
        debug=debug,
        log_file=log_file,
        store_script=store_script,
    )


def oop(line: str) -> bool:
    """
    Given a line, return True if the player acting is out of position
    >>> oop("r:0")
    True
    >>> oop("r:0:c")
    False
    >>> oop("r:0:c:c")
    True
    >>> oop("r:0")
    """
    last_street = line_to_streets(line)[-1]

    if last_street.startswith("r"):
        return last_street.count(":") % 2 == 1
    else:
        return last_street.count(":") % 2 == 0


def line_to_streets(line: str) -> List[str]:
    """
    Given a line in the gametree, break the line into a list
    of lines, one per street.

    :param line: A line in the gametree
    :returns: A root node if present (e.g., 'r:0'), and a list of lines, one per
        street

    # Example
    >>> line_to_streets("r:0:b125:b313:b501:c:c:c:c")
    ('r:0', [['b125', 'b313', 'b501', 'c'], ['c', 'c'], ['c']]
    """
    streets = []
    current_street = []
    split_line = line.split(":")
    root = ""
    if split_line[0] == "r":
        root = split_line[:2]
        split_line = split_line[2:]

    for action in split_line:
        current_street.append(action)
        if action.startswith("c") and len(current_street) > 1:
            streets.append(current_street)
            current_street = []

    if len(current_street) > 0:
        streets.append(current_street)
    return (root, streets)


def add_card_templates_to_line(line):
    """
    Given a line in the gametree, add templates ('{}') to the line where a
    chance node (e.g., a card), is expected. These templates can be used to
    add cards to a line to make a node id.

    :param line: A line in the gametree

    # Example
    >>> add_card_templates_to_line("r:0:b125:b313:b501:c:c:c:c")
    'r:0:b125:b313:b501:c:{}:c:c:{}:c'
    >>> add_card_templates_to_line("r:0:b125:b313:b501:c:c:c:c").format("Ks", "Qs")
    'r:0:b125:b313:b501:c:Ks:c:c:Qs:c'
    """
    if "{}" in line:
        return line

    streets = line_to_streets(line)
    return ":{}:".join(streets)


def streets_to_nodes(
    streets: List[str], dead_cards: List[str], isomorphism: bool = False
) -> List[str]:
    """
    Translate a list of streets representing a line to a list of nodes

    :param streets: The streets of a line to translate
    :param dead_cards: A list of cards that are not in the deck anymore (e.g., on the board)
    :param isomorphism: Whether to use suit isomorphism or not (not implemented)
    :returns: A list of all possible nodes that can be made from the line
    :raises NotImplementedError: If isomorphism is True
    :raises ValueError: If the line would contain more than 2 cards
    """
    if len(streets) > 3:
        raise ValueError(f"Cannot expand line with more than 3 streets: {streets}")
    for street in streets[:-1]:
        actions = street.split(":")
        if len(actions) < 1 or actions[-1] != "c":
            raise ValueError(f"All but last street must be complete: {streets}")
    if isomorphism:
        raise NotImplementedError("Suit isomorphism not implemented yet")
    available_cards = [c for c in CARDS if c not in dead_cards]
    templated_line = ":{}:".join(streets)
    num_cards = len(streets) - 1

    nodes = []
    if num_cards == 0:
        nodes.append(templated_line)
    elif num_cards == 1:
        for c in available_cards:
            nodes.append(templated_line.format(c))
    elif num_cards == 2:
        for c1 in available_cards:
            for c2 in available_cards:
                if c1 is not c2:
                    nodes.append(templated_line.format(c1, c2))
    else:
        raise ValueError(f"Cannot expand line with more than 2 cards: {streets}")
    return nodes


def lines_to_nodes(
    lines: List[str], dead_cards: Tuple[str], isomorphism: bool = False
) -> List[str]:
    """
    Expand a list of lines to all possible nodes associated with those lines.

    :param lines: A list of lines to expand to nodes
    :param dead_cards: A list of cards that are not in the deck anymore (e.g., on the board)
    :param isomorphism: Whether to use suit isomorphism or not (not implemented)
    :returns: A list of all possible nodes that can be made from the lines
    :raises NotImplementedError: If isomorphism is True
    :raises ValueError: If the line would contain more than 2 cards
    """

    nodes = []
    for line in lines:
        streets = line_to_streets(line)
        nodes.append(streets_to_nodes(streets, dead_cards, isomorphism))
    return nodes


def get_all_n_street_lines(lines: List[str], n: int) -> List[str]:
    return [line for line in lines if len(line_to_streets(line)) == n]


FLOP = 1
TURN = 2
RIVER = 3


def get_flop_lines(lines: List[str], current_street=FLOP) -> List[str]:
    return get_all_n_street_lines(lines, FLOP - current_street + 1)


def get_turn_lines(lines: List[str], current_street=FLOP) -> List[str]:
    return get_all_n_street_lines(lines, TURN - current_street + 1)


def get_river_lines(lines: List[str], current_street=FLOP) -> List[str]:
    return get_all_n_street_lines(lines, RIVER - current_street + 1)


def lock_overfold(lines: List[str], overfold_freq=0.01, position="OOP"):
    pass
