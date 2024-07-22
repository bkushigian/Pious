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
from pious.util import color_card, CARDS
from ansi.colour.rgb import rgb256
from ansi.colour.fx import reset, bold, crossed_out
from argparse import ArgumentParser

HORIZONTAL = "─"
VERTICAL = "│"
TOP_LEFT = "┌"
TOP_RIGHT = "┐"
BOTTOM_LEFT = "└"
BOTTOM_RIGHT = "┘"

COMBO_WEIGHT_THRESHOLD = 0.001

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

cards_to_print = args.cards
if cards_to_print is None:
    cards_to_print = CARDS
else:
    cards_to_print = cards_to_print.split()
    args.per_card = True


def linear_color_gradient(v, min=0.0, max=1.0, left=(255, 0, 0), right=(0, 255, 0)):
    # linear gradient along (255, 0, 0) and (255, 255, 255)
    max_n = max - min
    v_n = (v - min) / max_n
    # Normalize values to [0, 1]

    rgb = [0, 0, 0]
    # The first component moves from left[0] when v == 0 to right[0] when v == 1
    rgb[0] = (1 - v_n) * left[0] + v_n * right[0]
    rgb[1] = (1 - v_n) * left[1] + v_n * right[1]
    rgb[2] = (1 - v_n) * left[2] + v_n * right[2]
    rgb = rgb256(*rgb)
    return rgb


def print_card_banner(c, board):
    cards_in_board = []
    for b in board:
        cards_in_board.append(color_card(b))
    n_cards = len(cards_in_board)
    color_board = "".join(cards_in_board)
    board_len = n_cards * 2 + 1
    body = f"{color_card(c)}  on  [ {color_board} ]"
    body_len = 5 + 2 + 4 + board_len  # Compute by hand cuz ansi codes
    body_with_padding_len = body_len + 8  # 4 spacs per side
    s = f"""  ┌{'─' * body_with_padding_len}┐
-││{' ' * 4}{body}{' ' * 4}││-
  └{'─' * body_with_padding_len}┘ """
    lines = s.split("\n")
    l = len(lines[0])
    right_padding = (66 - len(lines[0])) // 2
    for line in lines:
        print(" " * right_padding + line)


def print_combo_equities(combos, width=3):
    i = 0
    row = []
    NUM_CHARS_IN_ROW = 11 * width
    print(TOP_LEFT + HORIZONTAL * NUM_CHARS_IN_ROW + TOP_RIGHT)
    print(f"{VERTICAL}{'BLOCKED COMBO EQUITIES':^{NUM_CHARS_IN_ROW}}{VERTICAL}")
    print(f"{VERTICAL}{'':^{NUM_CHARS_IN_ROW}}{VERTICAL}")
    for combo, combo_equity in combos:
        i += 1
        row.append(
            f"{color_combo(combo)}: {linear_color_gradient(combo_equity, 0.0, 1.0)}{combo_equity:4.2f}{reset} "
        )
        if i % width == 0:
            print(f'{VERTICAL} {"  ".join(row)} {VERTICAL}')
            row = []
    if len(row) > 0:
        print(
            f'{VERTICAL} {"  ".join(row)}{" " * (NUM_CHARS_IN_ROW - 11 * len(row))} {VERTICAL}'
        )
    print(BOTTOM_LEFT + HORIZONTAL * NUM_CHARS_IN_ROW + BOTTOM_RIGHT)


def print_histogram(hist, width=40):
    N = len(hist)
    total = sum(hist)
    if total < 0.0001:
        return
    y_delta = 100.0 / N
    bin_bound = 0.0
    HISTOGRAM_CHAR_WIDTH = (
        5
        + 3
        + width
        + 9
        + 2  # ' 10.0' \  # '%: '  # '**********'  # '( 39.92%)'  # $BORDERS
    )
    print(TOP_LEFT + HORIZONTAL * HISTOGRAM_CHAR_WIDTH + TOP_RIGHT)
    print(f"{VERTICAL}{'EQUITY_HISTOGRAM':^{HISTOGRAM_CHAR_WIDTH}}{VERTICAL}")
    print(f"{VERTICAL}{'':^{HISTOGRAM_CHAR_WIDTH}}{VERTICAL}")
    for row_idx in range(N):
        row_color = linear_color_gradient(
            bin_bound, 0.0, 90.0, (255, 0, 0), (0, 250, 0)
        )
        percent = hist[row_idx] / total
        n_chars = int(width * hist[row_idx] / total)
        row = f"{'█' * n_chars:{width}}"
        print(
            f"{VERTICAL}{row_color}{bin_bound:5.1f}%: {row}  {reset}({percent * 100.0:6.2f}%){VERTICAL}"
        )
        bin_bound += y_delta
    print(BOTTOM_LEFT + HORIZONTAL * HISTOGRAM_CHAR_WIDTH + BOTTOM_RIGHT)


def print_equity_delta_graph(
    equity_deltas,
    board,
    height=20,
):
    equity_deltas = sorted(equity_deltas, key=lambda x: x[1], reverse=True)
    combos, deltas = zip(*equity_deltas)
    min_delta, max_delta = min(deltas), max(deltas)
    delta_delta = max_delta - min_delta
    graph_height = [
        int(min(height * (d - min_delta) / delta_delta, height)) for d in deltas
    ]
    i = 0
    rows = []
    LAST_HEIGHT_DRAWN = height
    for h in range(height, -1, -1):
        row = [" " * i]
        rgb = linear_color_gradient(h, 0, height)
        drawn = False
        while i < len(graph_height) and graph_height[i] == h:
            if LAST_HEIGHT_DRAWN == h:
                char = HORIZONTAL
            elif LAST_HEIGHT_DRAWN > h:
                char = BOTTOM_LEFT

            row.append(f"{rgb}{char}{reset}")
            i += 1
            LAST_HEIGHT_DRAWN = h
            drawn = True
        if not drawn:
            row.append(f"{rgb}{VERTICAL}{reset}")
        rows.append("".join(row))

    delta_bin = max_delta
    delta_incr = delta_delta / height
    for row in rows:
        rgb = linear_color_gradient(delta_bin, min_delta, max_delta)
        prefix = f"{delta_bin*100:6.2f}"
        prefix = f"{rgb}{prefix}{reset} {VERTICAL} "  # Length is 9
        print(f"{prefix}{row}")
        delta_bin -= delta_incr
    print(f"       {BOTTOM_LEFT}{HORIZONTAL * len(deltas)}")
    print(f"        {''.join(color_card(c, True) for c in combos if c not in board)}")


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

equity_deltas, blocked_combos, histogram = blocker_effects(
    s, args.node_id, num_hist_bins=args.num_hist_bins
)
# Get effects as a list of key/value pairs, with the key being the card and the
# blocker value, and sorted from lowest to highest blocker value
equity_deltas = sorted(
    list(equity_deltas.items()), key=lambda x: x[1], reverse=not args.low_to_high
)
equity_deltas = [
    (card, eq_shift) for (card, eq_shift) in equity_deltas if card not in board
]

sizes = [x[1] for x in equity_deltas]
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
N = (len(equity_deltas) + args.cols - 1) // args.cols
for i in range(N):
    row = []
    rows.append(row)
    for j in range(args.cols):
        idx = i + j * N
        if idx >= len(equity_deltas):
            continue
        card, block_effect = equity_deltas[i + j * N]
        e = block_effect

        if card in board:
            s = f"{' ':6}"
            entry = f" {crossed_out(color_card(card,True))}  {s} "
        else:
            s = f"{e * 100:6.3f}"
            s = color_effect(e, s)
            entry = f"({color_card(card,True)}) {s}{bold('%')}"
        row.append(entry)


def color_combo(c):
    return f"{color_card(c[:2], True)}{color_card(c[2:], True)}"


if args.per_card:
    for c in histogram.keys():
        if c in board:
            continue
        if c not in cards_to_print:
            continue
        hist = histogram[c]
        combos = blocked_combos[c]
        if len(combos) == 0 or sum(hist) < COMBO_WEIGHT_THRESHOLD:
            continue
        print_card_banner(c, board)
        print_histogram(hist, width=47)
        combos.sort(key=lambda x: x[1], reverse=True)
        print_combo_equities(combos, width=6)

print_equity_delta_graph(equity_deltas, board)

print()
for row in rows:
    print("      " + "      ".join(row))
print()
