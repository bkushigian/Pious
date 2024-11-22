"""
This module is responsible for running aggregation reports. This does not
currently mimic PioSOLVER output format. Instead, it is an alternative
implementation.

This module is wrapped by the CLI command `pious execute`.
"""

from typing import Dict, List, Optional
from os import path as osp
import os
import pandas as pd
import numpy as np
import sys
import re

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


class LinesToAggregate:
    """
    A class describing the lines to aggregate. Created before a Solver instance
    is created, so we cannot iterate through lines and explicitly collect them
    (e.g., if we want to aggregate all flop lines, we need a solver instance).
    """

    def __init__(
        self, lines: Optional[List[Line]] = None, flop=False, turn=False, river=False
    ):
        self.lines = lines if lines is not None else []
        self.flop = flop
        self.turn = turn
        self.river = river

    @staticmethod
    def create_from(lines: "LinesToAggregate" | List[str] | str) -> "LinesToAggregate":
        ls = lines
        if isinstance(ls, list):
            # Case where a list of lines is passed
            ls = LinesToAggregate(lines=lines)
        elif isinstance(ls, str):
            # Case where a single line is passed
            ls = LinesToAggregate(lines=[lines])
        if not isinstance(ls, LinesToAggregate):
            raise ValueError(
                f"lines input must be of type List[str], str, or LinesToAggregate, but found {type(lines)}"
            )
        return ls


class AggregationConfig:
    """
    Configure an aggregation report.
    """

    def __init__(self, equities=True, evs=True, action_freqs=True, action_evs=False):
        self.equities = equities
        self.evs = evs
        self.action_evs = action_evs
        self.action_freqs = action_freqs


class CFRDatabase:
    def __init__(self, dir):
        self.dir = dir
        if not osp.isdir(dir):
            raise ValueError(f"Directory {dir} does not exist")
        self.dir_contents = os.listdir(dir)
        self.all_files = [f for f in self.dir_contents if osp.isfile(osp.join(dir, f))]
        self.cfr_files = [f for f in self.all_files if f.endswith(".cfr")]
        self.boards = [f.split(".")[0] for f in self.cfr_files]

        self.script_txt = osp.join(dir, "script.txt")
        if not osp.isfile(self.script_txt):
            self.script_txt = None

        self.raw_weights: Dict[str, float] = {}
        self._parse_board_weights_from_script()
        self.total_weights = sum(self.raw_weights.values())

        # Transform weights into board frequencies
        self.frequencies = {
            b: w / self.total_weights for (b, w) in self.raw_weights.items()
        }

    def get_weight(self, board: str):
        return self.raw_weights.get(board.strip(), 1.0)

    def _parse_board_weights_from_script(self):
        # Groups:
        # 0. Board
        # 1. Flop
        # 2. Turn (optional)
        # 3. River (optional)
        # 4. Weight
        pattern = re.compile(
            r"^#(([2-9AKQJT][scdh][2-9AKQJT][scdh][2-9AKQJT][scdh])([2-9AKQJT][scdh])?([2-9AKQJT][scdh])?)(?:(?::)(\d+|\d*\.\d+))$"
        )

        if self.script_txt is None:
            return
        with open(self.script_txt) as f:
            lines = f.readlines()
        for line in lines:
            m: re.Match = pattern.match(line.strip())
            if m:
                groups = m.groups()
                board = groups[0]
                weight = float(groups[4])
                self.raw_weights[board] = weight

    def get_cfr_files(self):
        """
        Return the paths of each CFR file by joining to dir
        """
        return [osp.join(self.dir, f) for f in self.cfr_files]

    def __iter__(self):
        for board, cfr_file in zip(self.boards, self.cfr_files):
            freq = self.frequencies[board]
            yield board, osp.join(self.dir, cfr_file), freq


def aggregate_files_in_dir(
    dir: str, lines: List[Line] | str | LinesToAggregate, conf: AggregationConfig = None
):
    if conf is None:
        conf = AggregationConfig()

    db = CFRDatabase(dir)
    if len(db.cfr_files) == 0:
        raise RuntimeError(f"No CFR files found in {dir}")

    # We want to collect lines. To do this we need a solver instance with a tree
    # loaded, so we will grab the first cfr file in the DB
    cfr0 = osp.join(db.dir, db.cfr_files[0])
    solver: Solver = make_solver()
    solver.load_tree(cfr0)

    ls = LinesToAggregate.create_from(lines)
    lines_to_aggregate = collect_lines_to_aggregate(solver, ls)
    reports = None
    reports_lines = None
    for board, cfr_file, freq in db:
        print(board, cfr_file, freq)
        new_reports = aggregate_single_file(cfr_file, lines, conf, freq)

        # One time update: This is necessary to perform sanity checking and
        # ensure that Each report has the same lines.
        if reports is None:
            reports = new_reports
            reports_lines = set(reports.keys())
            continue

        # Perform Sanity Check
        new_reports_lines = set(new_reports.keys())
        if reports_lines != new_reports_lines:
            sym_diff = reports_lines.symmetric_difference(new_reports_lines)
            raise RuntimeError(
                f"The following lines were not found in both reports: {sym_diff}"
            )

        # We know we have the same keyset, so combine the reports
        for line in new_reports:
            df1 = reports[line]
            df2 = new_reports[line]
            reports[line] = pd.concat([df1, df2], ignore_index=True)

    return reports


def aggregate_single_file(
    cfr_file: str,
    lines: List[Line] | str | LinesToAggregate,
    conf: AggregationConfig = None,
    weight: float = 1.0,
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
    ls = LinesToAggregate.create_from(lines)
    lines_to_aggregate = collect_lines_to_aggregate(solver, ls)

    return aggregate_lines_for_solver(solver, lines_to_aggregate, conf, weight)


def aggregate_lines_for_solver(
    solver: Solver,
    lines_to_aggregate: List[Line],
    conf: Optional[AggregationConfig] = None,
    weight: float = 1.0,
):
    if conf is None:
        conf = AggregationConfig()
    board = solver.show_board().split()

    reports: Dict[Line, pd.DataFrame] = {}

    for line in lines_to_aggregate:
        node_ids = line.get_node_ids(dead_cards=board)

        # Get the first node_id to compute some global stuff about the line
        node_id = node_ids[0]
        actions = solver.show_children_actions(node_id)
        node: Node = solver.show_node(node_id)
        pot = node.pot

        action_names = get_action_names(line, actions)

        # Compute columns
        columns = ["Flop", "Turn", "River"][: len(node.board) - 2]
        columns.append("Global Freq")

        sorted_actions = get_sorted_actions(actions)

        if conf.action_freqs:
            for a in sorted_actions:
                columns.append(f"{action_names[a]} Freq")
        if conf.action_evs:
            for a in sorted_actions:
                columns.append(f"{action_names[a]} EV")

        df = pd.DataFrame(columns=columns)
        reports[line] = df

        position = node.get_position()
        position_idx = node.get_position_idx()  # 0 for OOP, 1 for IP
        cp_money_so_far = pot[position_idx]

        for node_id in node_ids:
            row = get_runout(solver, node_id)

            global_freq = solver.calc_global_freq(node_id)
            row.append(global_freq * weight)

            action_to_strats = get_actions_to_strats(solver, node_id, actions)

            # Compute Frequencies
            if conf.action_freqs:
                row += get_action_freqs(
                    solver, node_id, position, sorted_actions, action_to_strats
                )

            if conf.action_evs:
                row += get_action_evs(
                    solver,
                    node_id,
                    position,
                    sorted_actions,
                    action_to_strats,
                    cp_money_so_far,
                )

            df.loc[len(df)] = row

    return reports


def collect_lines_to_aggregate(solver: Solver, lines: LinesToAggregate) -> List[Line]:
    """
    Select lines from `all_lines` that pass the filters specified in args.
    """
    all_lines = get_all_lines(solver)
    strs2lines = {l.line_str: l for l in all_lines}
    nonterminal_lines: List[Line] = filter_lines(all_lines, is_nonterminal)

    collected_lines = []

    if lines.flop:
        collected_lines += filter_lines(nonterminal_lines, is_flop)

    if lines.turn:
        collected_lines += filter_lines(nonterminal_lines, is_turn)

    if lines.river:
        collected_lines += filter_lines(nonterminal_lines, is_river)

    for line_str in lines.lines:
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


def get_action_names(line: Line, actions: List[str]) -> Dict[str, str]:
    """
    Map each action identifier (e.g., "b123") to a human-readable action name
    such as "Bet 123". This name depends on previous actions: the pio action
    identifier includes all accumulated chips put in play by the player in the
    hand. Thus, if a player bet 12 chips on the flop, a turn barrel of "b123"
    corresponds to "Bet 111".
    """
    action_names = {}
    facing_bet_or_raise = "f" in actions
    money_at_start_of_street = sum(line.money_in_per_street()[: line.current_street()])
    for a in actions:
        if a.startswith("b"):
            amount = int(a[1:]) - money_at_start_of_street
            bet_or_raise = "Raise" if facing_bet_or_raise else "Bet"
            action_names[a] = f"{bet_or_raise} {amount}"
        elif a == "f":
            action_names[a] = "Fold"
        elif a == "c":
            action_names[a] = "Call" if facing_bet_or_raise else "Check"
    return action_names


def get_sorted_actions(actions):
    # Sort action keys
    def action_key(s):
        if s.startswith("b"):
            return int(s[1:])
        elif s == "c":
            return 0
        else:
            return -1

    return sorted(actions, key=action_key)


def get_actions_to_strats(solver: Solver, node_id: str, actions: List[str]):
    strats_for_node = solver.show_strategy(node_id)
    actions_to_strats = {}
    for i, a in enumerate(actions):
        actions_to_strats[a] = np.array(strats_for_node[i])
    return actions_to_strats


def get_action_freqs(solver, node_id, position, sorted_actions, action_to_strats):
    row = []
    range = solver.show_range(position, node_id)
    total_combos = sum(range.range_array)
    if total_combos == 0.0:
        for a in sorted_actions:
            row.append(np.nan)
    else:
        for a in sorted_actions:
            # compute action frequency as the percentage of combos taking
            # this action
            x = 100.0 * np.dot(action_to_strats[a], range.range_array) / total_combos
            row.append(x)
    return row


def get_action_evs(
    solver, node_id, position, sorted_actions, action_to_strats, cp_money_so_far
):

    row = []
    evs, matchups = solver.calc_ev(position, node_id)
    evs = evs + cp_money_so_far
    total_matchups = sum(matchups)

    matchups = np.where(np.isnan(matchups), 0, matchups)
    matchups[np.isinf(matchups)] = 0.0
    evs = np.where(np.isnan(evs), 0, evs)
    evs[np.isinf(evs)] = 0.0
    # EVs
    if total_matchups == 0:
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
    return row


def get_runout(solver: Solver, node_id: str) -> List[str]:
    node = solver.show_node(node_id)
    b = node.board
    flop = b[:3]
    row = ["".join(flop)]
    if len(b) > 3:
        row.append(b[3])
    if len(b) > 4:
        row.append(b[4])
    return row
