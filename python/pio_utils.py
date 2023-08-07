"""
A collection of utility functions
"""

from typing import List
from pyosolver import PYOSolver


def add_chance_action_template_to_line(line):
    """Change a line to node template

    r:0:b125:b313:b501:c:c:c:c
         ^

    r:0:b125:b313:b501:c:{}:c:c:{}:c

    Args:
        line (_type_): _description_
    """
    l = line[2:]
    i = 0
    # First Street
    while i < len(l) - 1:
        if l[i].startswith("b") and l[i + 1].startswith("c"):
            # Call node
            l.insert(i + 2, "{}")
            i += 3
        elif l[i].startswith("c") and l[i + 1].startswith("c"):
            # Check check node
            l.insert(i + 2, "{}")
            i += 3
        else:
            i += 1
    return l


def expand_lines_to_nodes(lines: List[List[str]]):
    pass
