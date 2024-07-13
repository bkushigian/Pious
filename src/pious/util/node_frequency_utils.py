"""
This file contains utility functions for working with node frequencies
"""

from queue import PriorityQueue

from pious.pyosolver import PYOSolver, Node
from pious.traverser import bfs


class NodeFreqPriorityQueue:
    def __init__(self, solver, root_node_id="r:0"):
        self.solver = solver
        self.root_node_id = root_node_id
        self.queue: PriorityQueue = PriorityQueue()
        self.current_node_id = root_node_id


def map_frequency_boundry(
    solver: PYOSolver, node_id: str = "r:0", frequency_threshold: float = 0.1
):
    traverser = bfs(solver, node_id)
    pass
