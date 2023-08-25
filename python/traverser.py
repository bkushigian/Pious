""" 
Traverse a game tree
"""
from typing import Callable, List
from pyosolver import PYOSolver, Node
from queue import Queue


class Traverser:
    def __iter__(self):
        self.skip_function = lambda solver, node_id: False

    def with_skip_function(self, skip_function: Callable[[PYOSolver, str], bool]):
        self.skip_function = skip_function


class BFSolverTraverser(Traverser):
    def __init__(self, solver: PYOSolver, root_node_id="r:0"):
        self.solver: PYOSolver = solver
        self.root_node_id: str = root_node_id
        self.queue: Queue = Queue()
        self.queue.put(root_node_id)

    def __iter__(self):
        while not self.queue.empty():
            node_id = self.queue.get()
            node = self.solver.show_node(node_id)
            children = self.solver.show_children(node_id)
            for child in children:
                if not self.skip_function(self.solver, child.node_id):
                    self.queue.put(child)
            yield node


class DFSolverTraverser(Traverser):
    def __init__(self, solver: PYOSolver, root_node_id="r:0"):
        self.solver: PYOSolver = solver
        self.root_node_id: str = root_node_id
        self.stack: List[str] = [root_node_id]

    def __iter__(self):
        while len(self.stack) > 0:
            node_id = self.stack.pop()
            node = self.solver.show_node(node_id)
            children = self.solver.show_children(node_id)
            for child in children:
                if not self.skip_function(self.solver, child.node_id):
                    self.stack.append(child)
            yield node


def bfs(solver: PYOSolver, root_node_id: str = "r:0"):
    return BFSolverTraverser(solver, root_node_id=root_node_id)


def dfs(solver: PYOSolver, root_node_id: str = "r:0"):
    return DFSolverTraverser(solver, root_node_id=root_node_id)
