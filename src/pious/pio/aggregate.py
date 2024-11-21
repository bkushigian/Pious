"""
This module is responsible for running aggregation reports. This does not
currently mimic PioSOLVER output format. Instead, it is an alternative
implementation.

This module is wrapped by the CLI command `poius execute`.
"""

from typing import Dict, List, Optional
from os import path as osp
import pandas as pd
import numpy as np
import sys

from ..pio import (
    make_solver,
    Line,
    Node,
    Solver,
    get_all_lines,
    filter_lines,
    is_flop,
    is_turn,
    is_river,
    is_ip,
    is_oop,
    is_terminal,
    is_nonterminal,
)
from ..pio.line import ensure_line_root


np.set_printoptions(threshold=sys.maxsize, linewidth=200, precision=3)


def aggregate_single_file(
    cfr_file: str,
    lines: Optional[List[Line | str]] = None,
    flop=False,
    turn=False,
    river=False,
) -> pd.DataFrame:
    """
    Compute an aggregation report for the sim in `cfr_file` for each line in
    `lines_to_aggregate`

    TODO: handle partial saves
    TODO: what if line is not present?
    """
    file_name: str = cfr_file
    assert osp.isfile(file_name)
    if not file_name.endswith(".cfr"):
        print(f"{file_name} must be a .cfr file")
        exit(-1)
    solver: Solver = make_solver()
    solver.load_tree(file_name)
    lines_to_aggregate = collect_lines_to_aggregate(solver, lines, flop, turn, river)

    return aggregate_lines_for_solver(solver, lines_to_aggregate)


def aggregate_lines_for_solver(solver: Solver, lines_to_aggregate: List[Line]):
    board = solver.show_board().split()

    reports: Dict[Line, pd.DataFrame] = {}

    for line in lines_to_aggregate:
        node_ids = line.get_node_ids(dead_cards=board)

        # Get the first node_id to compute some global stuff about the line
        node_id = node_ids[0]
        actions = solver.show_children_actions(node_id)
        node: Node = solver.show_node(node_id)
        pot = node.pot

        facing_bet_or_raise = "f" in actions
        money_at_start_of_street = sum(
            line.money_in_per_street()[: line.current_street()]
        )

        action_names = {}  # map from action symbols to action names

        for a in actions:
            if a.startswith("b"):
                amount = int(a[1:]) - money_at_start_of_street
                bet_or_raise = "Raise" if facing_bet_or_raise else "Bet"
                action_names[a] = f"{bet_or_raise} {amount}"
            elif a == "f":
                action_names[a] = "Fold"
            elif a == "c":
                action_names[a] = "Call" if facing_bet_or_raise else "Check"

        # Compute columns
        columns = ["Flop"]
        if len(node.board) > 3:
            columns.append("Turn")
        if len(node.board) > 4:
            columns.append("River")

        columns.append("Global Freq")

        # Sort action keys
        def action_key(s):
            if s.startswith("b"):
                return int(s[1:])
            elif s == "c":
                return 0
            else:
                return -1

        sorted_actions = sorted(actions, key=action_key)
        for a in sorted_actions:
            columns.append(f"{action_names[a]} Freq")
        for a in sorted_actions:
            columns.append(f"{action_names[a]} EV")

        df = pd.DataFrame(columns=columns)
        reports[line] = df

        position = node.get_position()
        if position == "OOP":
            position_idx = 0
        else:
            position_idx = 1
        cp_money_so_far = pot[position_idx]
        print(cp_money_so_far)
        printed_already = False
        for node_id in node_ids:
            print(node_id)
            b = solver.show_node(node_id).board
            flop = b[:3]
            row = ["".join(flop)]
            if len(b) > 3:
                row.append(b[3])
            if len(b) > 4:
                row.append(b[4])

            global_freq = solver.calc_global_freq(node_id)
            row.append(global_freq)
            strats_for_node = solver.show_strategy(node_id)
            range = solver.show_range(position, node_id)

            total_combos = sum(range.range_array)

            evs, matchups = solver.calc_ev(position, node_id)
            evs = evs + cp_money_so_far
            total_matchups = sum(matchups)

            matchups = np.where(np.isnan(matchups), 0, matchups)
            matchups[np.isinf(matchups)] = 0.0
            evs = np.where(np.isnan(evs), 0, evs)
            evs[np.isinf(evs)] = 0.0
            if not printed_already:
                printed_already = True
                hand_order = solver.show_hand_order()
                print(node_id)
                for i, (hand, ev, matchups) in enumerate(
                    zip(hand_order, evs, matchups)
                ):
                    print(f"{i}. {hand}: {ev:06.4f} {matchups:08.6f}")
                print(position)

            action_to_strats = {}
            for i, a in enumerate(actions):
                action_to_strats[a] = np.array(strats_for_node[i])

            # Compute Frequencies
            if total_combos == 0.0:
                for a in sorted_actions:
                    row.append(np.nan)
            else:
                for a in sorted_actions:
                    # compute action frequency as the percentage of combos taking
                    # this action
                    x = (
                        100.0
                        * np.dot(action_to_strats[a], range.range_array)
                        / total_combos
                    )
                    row.append(x)

            # EVs
            if total_matchups == 0 or total_combos == 0.0:
                print("no matchups")
                for a in sorted_actions:
                    print("Adding nans")
                    row.append(np.nan)
            else:
                evs_dived = evs / total_matchups

                for a in sorted_actions:

                    strat = action_to_strats[a]
                    x = np.dot(np.multiply(matchups, strat), evs_dived)
                    row.append(x)

            df.loc[len(df)] = row

    return reports


def collect_lines_to_aggregate(
    solver: Solver, lines: List[Line], flop: bool, turn: bool, river: bool
) -> List[Line]:
    """
    Select lines from `all_lines` that pass the filters specified in args.
    """
    all_lines = get_all_lines(solver)
    strs2lines = {l.line_str: l for l in all_lines}
    nonterminal_lines: List[Line] = filter_lines(all_lines, is_nonterminal)

    collected_lines = []

    if flop:
        collected_lines += filter_lines(nonterminal_lines, is_flop)

    if turn:
        collected_lines += filter_lines(nonterminal_lines, is_turn)

    if river:
        collected_lines += filter_lines(nonterminal_lines, is_river)

    for line_str in lines:
        line_str = ensure_line_root(line_str)
        if line_str not in strs2lines:
            print(f"Unable to find line {line_str}")
            continue
        line = strs2lines[line_str]
        if is_terminal(line):
            print(f"Cannot aggregate terminal lines: {line}")
            continue
        if line not in collected_lines:
            collected_lines.append(line)

    return collected_lines
