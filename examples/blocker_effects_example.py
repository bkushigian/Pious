"""
This example computes blocker effects from an existing tree. This uses the
`pious.pio.blockers.compute_single_card_blocker_effects` function, which looks
at the per-hand equities at a given node and recompute's the non-active
player's equities for each dead card. This tells us how much equity shifts when
the opponent cannot have a given card.
"""

from pious.pio import (
    compute_single_card_blocker_effects as blocker_effects,
    make_solver,
    rebuild_and_resolve,
)
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("cfr_path")
parser.add_argument("node_id")
parser.add_argument(
    "--resolve",
    action="store_true",
    help="should we resolve the tree? useful for river nodes",
)

args = parser.parse_args()
node_id = args.node_id

s = make_solver()
s.load_tree(args.cfr_path)
node = s.show_node(node_id)

line = node.as_line_str()
s.load_all_nodes()
all_lines = s.show_all_lines()

if line not in all_lines:
    raise ValueError(f"Invalid line {line}")

if args.resolve:
    rebuild_and_resolve(s)

effects = blocker_effects(s, node_id)
# Get effects as a list of key/value pairs, with the key being the card and the
# blocker value, and sorted from lowest to highest blocker value
effects = sorted(list(effects.items()), key=lambda x: x[1])

for card, block_effect in effects:
    print(f"{card}: {block_effect * 100: 3.2f}% Equity")
