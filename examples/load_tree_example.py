"""
This example loads a test tree packaged in resources, loads all nodes, and
prints all lines.
"""

from pious.pio.util import make_solver
from pious.pio.resources import get_test_tree

solver = make_solver()
solver.load_tree(get_test_tree())  # Replace with your tree
solver.load_all_nodes()  # Required for partial saves in Pio3
tree_info = solver.show_tree_info()
print(f"Board: {tree_info['Board']}")
print(f"Pot: {tree_info['Pot']}")
print(f"EffectiveStacks: {tree_info['EffectiveStacks']}")

lines = solver.show_all_lines()
print("Last 10 lines:", lines[-10:])
