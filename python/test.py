import pio_utils
import pyosolver
from argparse import ArgumentParser

from os import path as osp

path = osp.join(
    osp.dirname(__file__), "..", "resources", "trees", "CO_9s6h2h_small.cfr"
)
path2 = r"C:\PioSOLVER\Saves\7s6s3h-flop.cfr"

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

all_lines = solver.show_all_lines()

flop_lines = pio_utils.get_flop_lines(lines=all_lines, current_street=pio_utils.FLOP)

print("FLOP LINES")
for line in flop_lines:
    print(line)

turn_lines = pio_utils.get_turn_lines(lines=all_lines, current_street=pio_utils.FLOP)

print("TURN LINES")
for line in turn_lines[:10]:
    print(line)

print("RIVER LINES")
river_lines = pio_utils.get_river_lines(lines=all_lines, current_street=pio_utils.FLOP)
for line in river_lines[:10]:
    print(line)


print("NODES FOR A LINE")
for nodes_for_line in pio_utils.lines_to_nodes(
    lines=["r:0:c:b125:b330:c:c:c:c:b750:f"], dead_cards=board
):
    for node in nodes_for_line[:30]:
        print(node)
