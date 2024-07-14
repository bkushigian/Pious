from argparse import ArgumentParser
import time
from os import path as osp

from pious.pio.util import make_solver
from pious.pio import solver
from pious.pio.line import (
    Line,
    FLOP,
    get_flop_lines,
    get_turn_lines,
    get_river_lines,
)

from pkg_resources import resource_filename, resource_listdir

cfr_path = resource_filename("pious.pio.resources.trees", "Kh7h2c.cfr")

parser = ArgumentParser()
parser.add_argument("--path", "-p", type=str, default=cfr_path)
parser.add_argument("--log_file", "-l", type=str, default=None)
parser.add_argument("--debug", "-d", action="store_true")
parser.add_argument("--store_script", "-s", action="store_true")

args = parser.parse_args()

t0 = time.time()
if not osp.exists(args.path):
    raise RuntimeError(f"Tree path {args.path} does not exist")

solver = make_solver(
    debug=args.debug, log_file=args.log_file, store_script=args.store_script
)
solver.load_tree(f'"{args.path}"')
t_load_tree = time.time()
print(f"Loaded tree from {args.path} in {t_load_tree - t0:.2f} seconds")
print(f"Board: {solver.show_node('r:0').board}")


root_node_info = solver.show_node("r:0")
board = root_node_info.board
print("Board:", board)

t_0 = time.time()
solver.load_all_nodes()
all_lines = solver.show_all_lines()
t_get_all_lines = time.time()

print(f"Found {len(all_lines)} lines in {t_get_all_lines - t_0:.2f} seconds")

t_0 = time.time()
all_lines = [Line(line, starting_street=FLOP) for line in solver.show_all_lines()]

print(f"Created {len(all_lines)} Line objects in {time.time() - t_0:.2f} seconds")

t_0 = time.time()
flop_lines = get_flop_lines(lines=all_lines)
t_flop_lines = time.time()

print(f"Found {len(flop_lines)} FLOP LINES in {t_flop_lines - t_0:.2f} seconds")
for line in flop_lines[:10]:
    print(line.streets_as_lines)
print("...")
print()

t_0 = time.time()
turn_lines = get_turn_lines(lines=all_lines)
t_turn_lines = time.time()
print(f"Found {len(turn_lines)} TURN LINES in {t_turn_lines - t_0:.2f} seconds")

for line in turn_lines[:10]:
    print(line.streets_as_lines)
print("...")
print()

t_0 = time.time()
river_lines = get_river_lines(lines=all_lines)
t_river_lines = time.time()
print(f"Found {len(river_lines)} RIVER LINES in {t_river_lines - t_0:.2f} seconds")

for line in river_lines[:10]:
    print(line.streets_as_lines)
print("...")
print()

print("Total lines per street:")
print(f"Flop: {len(flop_lines)}")
print(f"Turn: {len(turn_lines)}")
print(f"River: {len(river_lines)}")
print(f"Total: {len(flop_lines) + len(turn_lines) + len(river_lines)}")
print(f"Expected: {len(all_lines)}")
print()

print("Expanding all lines to nodes...")
t_0 = time.time()
nodes_per_line = [line.get_node_ids(dead_cards=board) for line in all_lines]
t_expand_all_nodes = time.time()

total_nodes = sum([len(nodes) for nodes in nodes_per_line])

print(
    f"Expanded all lines to {total_nodes} nodes in {t_expand_all_nodes - t_0:.2f} seconds"
)
