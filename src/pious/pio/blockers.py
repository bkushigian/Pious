"""
A module for computing various blocker effects
"""

from .solver import Node, Solver
from .equity import EquityCalculator
from ..util import (
    CARDS,
    PIO_HAND_ORDER,
    SUIT_ORDER,
    color_card,
    color_suit,
    get_card_index_array,
)
from ansi.colour.rgb import rgb256
from ansi.colour.fx import reset, bold, crossed_out
import numpy as np


def compute_single_card_blocker_effects(
    solver: Solver, node_id: str | Node, num_hist_bins: int = 10
):
    """
    Compute blocking effects of each card in the current player's range.
    Here, higher is better and lower is worse.
    """
    # We don't care about position other than determining which range we are
    # looking at. The hero's range is the current player to act. So we use the
    # current position only to ensure we have the right player's range
    # associated with hero

    node: Node = solver.show_node(node_id)
    pos = node.get_position()
    board = node.board
    hero_is_oop = pos == "OOP"

    hero_range = solver.show_range("IP", node_id)
    villain_range = solver.show_range("OOP", node_id)

    if hero_is_oop:
        hero_range, villain_range = villain_range, hero_range

    # We now have hero and villain's range correctly assigned.  Since position
    # doesn't matter in equity calculations, so we assume that hero is OOP in
    # the equity calculator

    eqc = EquityCalculator(board, oop_range=hero_range, ip_range=villain_range)

    # Get villain equity information (ip)
    equities, matchups, total = eqc.compute_hand_equities(oop=False)
    equities = np.nan_to_num(equities, 0.0)  # Remove nans

    base_villain_equity2 = sum(equities * matchups) / sum(matchups)

    equity_deltas = {}
    blocked_combos = {}
    histograms = {}

    for c in CARDS:
        indicator_array = get_card_index_array(c, negate=False)
        mask_array = get_card_index_array(c, negate=True)

        # First, compute individual equity deltas for this card
        eqs = equities * mask_array
        mus = matchups * mask_array
        eq = sum(eqs * mus) / sum(mus)
        diff = base_villain_equity2 - eq
        equity_deltas[c] = diff

        # Next, collect the blocked combos and their equities
        blocked_combos[c] = [
            (PIO_HAND_ORDER[idx], equities[idx])
            for (idx, indicator) in enumerate(indicator_array)
            if indicator == 1.0 and matchups[idx] > 0.0
        ]

        # Finally, break the equities of the blocked combos into a histogram
        num_hist_bins = min(max(1, num_hist_bins), 20)
        hist = np.zeros(shape=num_hist_bins, dtype=np.float64)
        total_matchups = sum(matchups)
        for idx, indicator in enumerate(indicator_array):
            if indicator == 0.0 or matchups[idx] == 0.0:
                continue
            e = equities[idx]
            hist_bin = min(int(e * num_hist_bins), num_hist_bins - 1)
            hist[hist_bin] = matchups[idx] / total_matchups
        histograms[c] = hist

    return SingleCardBlockerEffects(
        board, node_id, equity_deltas, blocked_combos, histograms
    )


class SingleCardBlockerEffects:
    def __init__(self, board, node, equity_deltas, blocked_combos, histograms):
        self.equity_deltas = equity_deltas
        self.node = node
        self.blocked_combos = blocked_combos
        self.histograms = histograms
        self.board = board

    def print_histogram(self, card, width=40):
        hist = self.histograms[card]
        print_card_banner(card, self.board)
        print_histogram(hist, width=width)

    def print_per_card(self, cards_to_print=None):
        print_per_card_data(
            self.histograms,
            self.board,
            self.blocked_combos,
            cards_to_print=cards_to_print,
        )

    def print_graph(self, height=20, print_suits=False):
        print_equity_delta_graph(
            list(self.equity_deltas.items()),
            self.board,
            height=height,
            print_suits=print_suits,
        )

    def print_grid(self, cell_width=7):
        print_blocker_effects_by_rank_suit(
            list(self.equity_deltas.items()), cell_width=cell_width
        )

    def print_list(self, cols=4, use_same_scale=True):
        print_blocker_effects_by_card(
            sorted(list(self.equity_deltas.items()), key=lambda x: x[1]),
            board=self.board,
            cols=cols,
            use_same_scale=use_same_scale,
        )

    def __call__(self, card, width=40):
        self.print_histogram(card, width=width)


def linear_color_gradient(
    v, min=0.0, max=1.0, left=(255, 0, 0), right=(0, 255, 0), bg=False
):
    # linear gradient along (255, 0, 0) and (255, 255, 255)
    max_n = max - min
    v_n = (v - min) / max_n
    # Normalize values to [0, 1]

    rgb = [0, 0, 0]
    # The first component moves from left[0] when v == 0 to right[0] when v == 1
    rgb[0] = (1 - v_n) * left[0] + v_n * right[0]
    rgb[1] = (1 - v_n) * left[1] + v_n * right[1]
    rgb[2] = (1 - v_n) * left[2] + v_n * right[2]
    rgb = rgb256(rgb[0], rgb[1], rgb[2], bg=bg)
    return rgb


def color_combo(c):
    return f"{color_card(c[:2], True)}{color_card(c[2:], True)}"


HORIZONTAL = "─"
VERTICAL = "│"
TOP_LEFT = "┌"
TOP_RIGHT = "┐"
BOTTOM_LEFT = "└"
BOTTOM_RIGHT = "┘"

TOP_LEFT_ROUND = "╭"
TOP_RIGHT_ROUND = "╮"
BOTTOM_LEFT_ROUND = "╰"
BOTTOM_RIGHT_ROUND = "╯"

LEFT_T = "├"
RIGHT_T = "┤"
TOP_T = "┬"
BOTTOM_T = "┴"
CROSS = "┼"

COMBO_WEIGHT_THRESHOLD = 0.001


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
    s = f"""  ╭{'─' * body_with_padding_len}╮
-││{' ' * 4}{body}{' ' * 4}││-
  ╰{'─' * body_with_padding_len}╯ """
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


def print_equity_delta_graph(equity_deltas, board, height=20, print_suits=False):
    equity_deltas = sorted(equity_deltas, key=lambda x: x[1], reverse=True)
    equity_deltas = [
        (combo, delta) for (combo, delta) in equity_deltas if combo not in board
    ]
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
        if print_suits:
            row = [" " * 2 * i]
        else:
            row = [" " * 1 * i]
        rgb = linear_color_gradient(h, 0, height)
        drawn = False
        while i < len(graph_height) and graph_height[i] == h:
            if LAST_HEIGHT_DRAWN == h:
                char = HORIZONTAL
            elif LAST_HEIGHT_DRAWN > h:
                char = BOTTOM_LEFT_ROUND

            if print_suits:
                row.append(f"{rgb}{char}{HORIZONTAL}{reset}")
            else:
                row.append(f"{rgb}{char}{reset}")

            i += 1
            LAST_HEIGHT_DRAWN = h
            drawn = True
        if not drawn:
            row.append(f"{rgb}{VERTICAL}{reset}")
        elif h > 0:
            row.append(f"{rgb}{TOP_RIGHT_ROUND}{reset}")
        rows.append("".join(row))

    delta_bin = max_delta
    delta_incr = delta_delta / height
    for row in rows:
        rgb = linear_color_gradient(delta_bin, min_delta, max_delta)
        prefix = f"{delta_bin*100:6.2f}"
        prefix = f"{rgb}{prefix}{reset} {VERTICAL}"  # Length is 9
        print(f"{prefix}{row}")
        delta_bin -= delta_incr
    if print_suits:
        print(f"       {BOTTOM_LEFT}{HORIZONTAL*2*len(deltas)}")
    else:
        print(f"       {BOTTOM_LEFT}{HORIZONTAL*1*len(deltas)}")
    print(
        f"        {''.join(color_card(c, not print_suits) for c in combos if c not in board)}"
    )


def print_blocker_effects_by_rank_suit(equity_deltas, cell_width=7):
    delta_lookup = {c: delta for (c, delta) in equity_deltas}
    deltas = list(delta_lookup.values())
    max_delta = max(deltas)
    min_delta = min(deltas)
    rows = []
    for rank in "AKQJT98765432":
        row = []
        for suit in SUIT_ORDER:
            card = f"{rank}{suit}"
            delta = delta_lookup.get(card, None)
            if delta:
                color = linear_color_gradient(delta, min_delta, max_delta, bg=True)
            else:
                color = rgb256(0, 0, 0)
            row.append((rank, suit, color, delta))
        rows.append(row)

    HOR_SEG = f"{HORIZONTAL*cell_width}"
    TOP_HOR_LINE = f"{TOP_LEFT}{HOR_SEG}{TOP_T}{HOR_SEG}{TOP_T}{HOR_SEG}{TOP_T}{HOR_SEG}{TOP_RIGHT}"
    CENTER_HOR_LINE = (
        f"{LEFT_T}{HOR_SEG}{CROSS}{HOR_SEG}{CROSS}{HOR_SEG}{CROSS}{HOR_SEG}{RIGHT_T}"
    )
    BOT_HOR_LINE = f"{BOTTOM_LEFT}{HOR_SEG}{BOTTOM_T}{HOR_SEG}{BOTTOM_T}{HOR_SEG}{BOTTOM_T}{HOR_SEG}{BOTTOM_RIGHT}"
    print(
        f"     {color_suit('s', width=cell_width)} {color_suit('h', width=cell_width)} {color_suit('d', width=cell_width)} {color_suit('c', width=cell_width)} "
    )
    print(f"    {TOP_HOR_LINE}")
    for i, row in enumerate(rows):
        rank = row[0][0]
        EMPTY_ROW_LINE = f"       {VERTICAL}"
        DELTA_ROW_LINE = f"{bold}{rank}{reset} {VERTICAL}"
        for rank, suit, color, delta in row:

            padding = f"{color}{' '*cell_width}{reset}"
            EMPTY_ROW_LINE += f"{padding}{VERTICAL}"
            if delta is None:
                # print empty cell
                DELTA_ROW_LINE += f"{padding}{VERTICAL}"
            else:
                delta_s = f"{color}{bold}{delta*100:^{cell_width}.1f}{reset}"
                # print delta
                DELTA_ROW_LINE += f"{delta_s}{VERTICAL}"
        print(f"  {DELTA_ROW_LINE}")
        if i < len(rows) - 1:
            print(f"    {CENTER_HOR_LINE}")
    print(f"    {BOT_HOR_LINE}")


def print_per_card_data(histogram, board, blocked_combos, cards_to_print=None):
    if cards_to_print is None:
        cards_to_print = CARDS
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


def color_effect(e, s, min_effect, max_effect):
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


def print_blocker_effects_by_card(equity_deltas, board, cols=4, use_same_scale=True):
    sizes = [x[1] for x in equity_deltas]
    min_effect = min(sizes)
    max_effect = max(sizes)
    abs_effect = max(abs(min_effect), abs(max_effect))
    if use_same_scale:
        min_effect = -abs_effect
        max_effect = abs_effect

    rows = []
    N = (len(equity_deltas) + cols - 1) // cols
    for i in range(N):
        row = []
        rows.append(row)
        for j in range(cols):
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
                s = color_effect(e, s, min_effect, max_effect)
                entry = f"({color_card(card,True)}) {s}{bold('%')}"
            row.append(entry)

    for row in rows:
        print("      " + "      ".join(row))
    print()
