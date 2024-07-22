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
from pious.util import color_card
from ansi.colour.rgb import rgb256
from ansi.colour.fx import reset, bold, crossed_out
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("cfr_path")
parser.add_argument("node_id")
parser.add_argument(
    "--resolve",
    action="store_true",
    help="should we resolve the tree? useful for river nodes",
)
parser.add_argument("--cols", type=int, default=4, help="Number of columns to display")
parser.add_argument(
    "--low_to_high",
    action="store_true",
    help="Display cards from lowest equity blocker effect to highest equity blocker effect",
)
parser.add_argument("--use_same_scale", action="store_true")

args = parser.parse_args()

s = make_solver()
s.load_tree(args.cfr_path)
node = s.show_node(args.node_id)
board = node.board

s.load_all_nodes()
all_lines = s.show_all_lines()

line = node.as_line_str()
if line not in all_lines:
    raise ValueError(f"Invalid line {line}")

if args.resolve:
    rebuild_and_resolve(s)

effects = blocker_effects(s, args.node_id)
# Get effects as a list of key/value pairs, with the key being the card and the
# blocker value, and sorted from lowest to highest blocker value
effects = sorted(
    list(effects.items()), key=lambda x: x[1], reverse=not args.low_to_high
)
effects = [(card, eq_shift) for (card, eq_shift) in effects if card not in board]

sizes = [x[1] for x in effects]
min_effect = min(sizes)
max_effect = max(sizes)
abs_effect = max(abs(min_effect), abs(max_effect))
if args.use_same_scale:
    min_effect = -abs_effect
    max_effect = abs_effect


def color_effect(e, s):
    if e < 0:
        # linear gradient along (255, 0, 0) and (255, 255, 255)
        scale = int((1 - e / min_effect) * 255)
        rgb = rgb256(255, scale, scale)
    elif e > 0:
        # linear gradient along (0, 255, 0) and (255, 255, 255)
        scale = int((1 - e / max_effect) * 255)
        rgb = rgb256(scale, 255, scale)
    else:
        rgb = rgb256(255, 255, 255)
    msg = (rgb, s, reset)
    return "".join([str(x) for x in msg])


rows = []
N = (len(effects) + args.cols - 1) // args.cols
for i in range(N):
    row = []
    rows.append(row)
    for j in range(args.cols):
        idx = i + j * N
        if idx >= len(effects):
            continue
        card, block_effect = effects[i + j * N]
        e = block_effect

        if card in board:
            s = f"{' ':6}"
            entry = f" {crossed_out(color_card(card))}  {s} "
        else:
            s = f"{e * 100:6.3f}"
            s = color_effect(e, s)
            entry = f"({color_card(card)}) {s}{bold('%')}"
        row.append(entry)

print()
for row in rows:
    print("      ".join(row))
print()
