"""
A collection of utility functions
"""

from typing import List
from pyosolver import PYOSolver

CARDS = tuple(f"{r}{s}" for r in "23456789TJQKA" for s in "shdc")


def add_card_templates_to_line(line):
    """
    Given a line in the gametree, add templates ('{}') to the line where a
    chance node (e.g., a card), is expected. These templates can be used to
    add cards to a line to make a node id.

    :param line: A line in the gametree

    # Example
    >>> add_card_templates_to_line("r:0:b125:b313:b501:c:c:c:c")
    "r:0:b125:b313:b501:c:{}:c:c:{}:c"
    >>> add_card_templates_to_line("r:0:b125:b313:b501:c:c:c:c:c").format("Ks", "Qs")
    "r:0:b125:b313:b501:c:Ks:c:c:Qs:c"
    """
    l = line.split(":")
    i = 0
    if l[0] == "r":
        i = 2
    # Invariant: the current node is not the last node in the street
    while i < len(l) - 2:
        if l[i + 1].startswith("c"):
            # Call node
            l.insert(i + 2, "{}")
            i += 2
        i += 1
    return ":".join(l)


def expand_line_to_nodes(
    line: str, dead_cards: List[str], isomorphism: bool = False
) -> List[str]:
    """
    Expand a line to all possible nodes

    :param line: The line to expand to a node
    :param dead_cards: A list of cards that are not in the deck anymore (e.g., on the board)
    :param isomorphism: Whether to use suit isomorphism or not (not implemented)
    :returns: A list of all possible nodes that can be made from the line
    :raises NotImplementedError: If isomorphism is True
    :raises ValueError: If the line would contain more than 2 cards
    """
    if isomorphism:
        raise NotImplementedError("Suit isomorphism not implemented yet")
    available_cards = [c for c in CARDS if c not in dead_cards]
    templated_line = add_card_templates_to_line(line)
    num_cards = templated_line.count("{}")
    print(f"Templated line: {templated_line}")
    print(f"Num cards: {num_cards}")
    print(f"Available cards: {available_cards}")

    nodes = []
    if num_cards == 0:
        nodes.append(templated_line)
    if num_cards == 1:
        for c in available_cards:
            nodes.append(templated_line.format(c))
    if num_cards == 2:
        for c1 in available_cards:
            for c2 in available_cards:
                if c1 is not c2:
                    nodes.append(templated_line.format(c1, c2))
    if num_cards >= 3:
        raise ValueError(f"Cannot expand line with more than 2 cards to come: {line}")
    print(f"Expanded to {len(nodes)} nodes")
    return nodes


def expand_lines_to_nodes(
    lines: List[str], dead_cards: List[str], isomorphism: bool = False
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
        nodes.append(expand_line_to_nodes(line, dead_cards, isomorphism))
    return nodes
