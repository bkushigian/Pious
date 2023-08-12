import pio_utils
import pyosolver
from argparse import ArgumentParser

from os import path as osp

path = osp.join(osp.dirname(__file__), "..", "resources", "trees", "7s5s3h_small.cfr")

parser = ArgumentParser()
parser.add_argument("--path", "-p", type=str, default=path)
parser.add_argument("--log_file", "-l", type=str, default=None)
parser.add_argument("--debug", "-d", action="store_true")
parser.add_argument("--store_script", "-s", action="store_true")

args = parser.parse_args()


solver = pio_utils.make_solver(
    debug=args.debug, log_file=args.log_file, store_script=args.store_script
)
solver.load_tree(args.path)
root_node_info = solver.show_node("r:0")
board = root_node_info["board"]
print("Board:", board)

all_lines = [
    pio_utils.Line(line, starting_street=pio_utils.FLOP)
    for line in solver.show_all_lines()
]

flop_lines = pio_utils.get_flop_lines(lines=all_lines)

print("FLOP LINES")
for line in flop_lines:
    print(line.streets_as_lines)

turn_lines = pio_utils.get_turn_lines(lines=all_lines)

print("TURN LINES")
for line in turn_lines[:10]:
    print(line.streets_as_lines)

print("RIVER LINES")
river_lines = pio_utils.get_river_lines(lines=all_lines)
for line in river_lines[:10]:
    print(line.streets_as_lines)


print("NODES FOR A LINE")
line = river_lines[0]
nodes = line.get_nodes(
    dead_cards=[card for card in pio_utils.CARDS if card not in ["Ah", "Kh", "Qh"]]
)
for node in nodes:
    print(node)
