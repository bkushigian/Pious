"""
This example computes blocker effects from an existing tree. This uses the
`pious.pio.blockers.compute_single_card_blocker_effects` function, which looks
at the per-hand equities at a given node and recompute's the non-active
player's equities for each dead card. This tells us how much equity shifts when
the opponent cannot have a given card.
"""

from argparse import ArgumentParser
from pious.pio import compute_single_card_blocker_effects, make_solver


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
parser.add_argument("--per_card", action="store_true", help="Print a per-card summary")
parser.add_argument("--cards", default=None, help="cards to print info on")
parser.add_argument(
    "--num_hist_bins",
    default=10,
    type=int,
    help="Number of bins to break histogram into",
)

args = parser.parse_args()

print_per_card_data = args.per_card
if args.cards is not None:
    print_per_card_data = True
cards_to_print = args.cards

solver = make_solver()
solver.load_tree(args.cfr_path)
effects = compute_single_card_blocker_effects(solver, args.node_id, args.num_hist_bins)

if print_per_card_data:
    effects.print_per_card(cards_to_print=cards_to_print)
effects.print_graph()
effects.print_grid()
effects.print_list()
