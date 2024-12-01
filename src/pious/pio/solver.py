"""
This file is taken from https://github.com/weston/pyosolver. I've modified it to
suit my needs.
"""

import subprocess
import os
from os import path as osp
from typing import List, Optional, Tuple
import numpy as np


from .tree_building import try_value_as_int, try_value_as_literal
from ..util import CARDS
from ..range import Range


class Node:
    def __init__(self, raw_node_data: str):
        self._raw_node_data = raw_node_data

        items = raw_node_data.strip().split("\n")
        self.node_id = items[0].strip()
        self.last_action = self.node_id.split(":")[-1]
        self.node_type = items[1].strip().split(" ")[0]
        self.board = tuple(items[2].strip().split(" "))
        self.pot = tuple([int(x) for x in items[3].strip().split(" ")])
        self.num_children = int(items[4].strip().split(" ")[0])
        self.flags = tuple(items[5].split(":")[1].strip().split(" "))

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"Node({self.node_id}, {self.node_type}, {self.board}, {self.pot}, {self.num_children}, {self.flags})"

    def get_position(self):
        try:
            return normalize_position(self.node_type)
        except ValueError:
            return None

    def get_position_idx(self):
        pos = self.get_position()
        if pos is None:
            raise ValueError("Invalid Node")
        if pos == "OOP":
            return 0
        elif pos == "IP":
            return 1
        else:
            raise ValueError(f"Invalid Position {pos}")

    def as_line_str(self) -> str:

        items = self.node_id.split(":")
        items = [a for a in items if a not in CARDS]
        return ":".join(items)


def normalize_position(pos):
    if isinstance(pos, int):
        if pos == 0:
            pos = "OOP"
        elif pos == 1:
            pos = "IP"
        else:
            raise ValueError(
                f"Invalid position int {pos}: must be 0 for OOP or 1 for IP"
            )
    elif isinstance(pos, str):
        pos2 = pos.upper()
        if pos2 == "OOP" or pos2 == "IP":
            return pos2
        elif pos2 == "OOP_DEC":
            return "OOP"
        elif pos2 == "IP_DEC":
            return "IP"
        else:
            raise ValueError(f'Invalid position str {pos}: must be "OOP" or "IP"')
    else:
        raise ValueError(
            f"Invalid position {pos}: must be int (0 or 1) or str (OOP or IP)"
        )


class Solver(object):
    def __init__(
        self,
        path,
        executable_name,
        debug=False,
        log_file=None,
        store_script=False,
        simulate=False,
        end_string="END",
    ):
        self.log_file = log_file
        if log_file is not None:
            self.log_file = open(log_file, "w")
        self.store_script = store_script
        self.commands = []
        self.debug = debug
        self.cfr_file_path = None
        self.solver_path = path
        self.executable_name = executable_name
        self.end_string = end_string
        self.simulate = simulate
        self.process = subprocess.Popen(
            [os.path.join(self.solver_path, self.executable_name)],
            cwd=self.solver_path,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            encoding="utf8",
        )

        self._run("set_end_string", self.end_string)
        self._run("set_threads", "0")
        self._run("set_recalc_accuracy", "0.0025 0.001 0.005")
        self._run("set_accuracy", "20")
        self._run("set_always_recalc", "0 60000")
        self._run("is_ready")

    def reset(self):
        self.process = subprocess.Popen(
            [os.path.join(self.solver_path, self.executable_name)],
            cwd=self.solver_path,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            encoding="utf8",
        )

    def is_ready(self):
        return self._run("is_ready")

    def echo(self, *args):
        return self._run("echo", *args)

    def load_tree(self, cfr_file_path: str, load_type=None):
        if load_type is not None:
            if load_type == "full" or load_type == "fast" or load_type == "auto":
                pass
            else:
                raise ValueError(
                    f"Illegal load type: must be 'full', 'fast', 'auto', or None"
                )
        cfr_file_path = cfr_file_path.strip()
        cfr_file_path = osp.abspath(cfr_file_path)

        if not osp.exists(cfr_file_path):
            raise FileNotFoundError(cfr_file_path)

        self.cfr_file_path = cfr_file_path

        # Now, quote the `cfr_file_path`
        quoted_cfr_file_path = f'"{cfr_file_path}"'

        if load_type is None:
            self._run("load_tree", quoted_cfr_file_path)
        else:
            self._run("load_tree", quoted_cfr_file_path, load_type)
        self.root_node_info = self.show_node("r:0")
        if self.debug:
            print(f"root_node_info: {self.root_node_info}\n")

    def show_node(self, node_id: str | Node) -> Optional[Node]:
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        data = self._run("show_node", node_id)
        if "ERROR" in data:
            raise ValueError(f"Could not find node_id {node_id}")
        return Node(data)

    def show_children(self, node_id: str | Node) -> List[Node]:
        """
        Return a list of children of the given specified node.
        """
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        data = self._run("show_children", node_id)
        if "ERROR" in data:
            return []
        if data.strip() == "":
            return []
        children_lines = data.split("\n\n")
        children = []
        # From the docs, each child entry is of the form:
        # 'child n:' nodeID NODE_TYPE board pot children_no 'flags: f1 f2'
        for child_line in children_lines:
            items = child_line.split("\n")
            node_data = items[1:]
            child_node = Node("\n".join(node_data))
            children.append(child_node)

        return children

    def show_children_actions(self, node_id: str | Node) -> List[str]:
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        data = self._run("show_children", node_id)
        if "ERROR" in data:
            return []
        if data.strip() == "":
            return []
        children_lines = data.split("\n\n")
        return [child.split("\n")[1].strip().split(":")[-1] for child in children_lines]

    def show_hand_order(self):
        return self._run("show_hand_order").split(" ")

    def set_accuracy(self, accuracy: float, accuracy_type: str = "chips"):
        acc_type = accuracy_type.lower()
        if acc_type != "fraction" and acc_type != "chips":
            raise ValueError(
                f"Illegal accuracy type: {accuracy_type}: expected 'chip s' or 'fraction'"
            )
        self._run("set_accuracy", str(accuracy), acc_type)

    def go(self, steps=None, units="seconds", quiet=False):
        command = ["go"]
        if steps is not None:
            command += [str(steps), units]
        response = self._run(*command)
        output = self._get_solver_output(trigger_word="SOLVER: stopped (", quiet=quiet)
        return response + "\n" + output

    def stop(self):
        return self._run("stop")

    def wait_for_solver(self):
        return self._run("wait_for_solver")

    def rebuild_forgotten_streets(self):
        return self._run("rebuild_forgotten_streets")

    def estimate_rebuild_forgotten_streets(self):
        response = self._run("estimate_rebuild_forgotten_streets")
        return response

    def reset_tree_info(self):
        return self._run("reset_tree_info")

    def add_info_line(self, info_line):
        return self._run("add_info_line", info_line)

    def show_board_no_iso(self):
        """
        Show the board without any isomorphisms set
        """
        return self._run("show_board_no_iso")

    def show_board(self):
        """
        Show the board without any isomorphisms set (alias for show_board_no_iso())
        """
        return self.show_board_no_iso()

    def show_tree_info(self):
        data = {}
        self._run("show_tree_info")
        for line in self._run("show_tree_info").split("\n"):
            try:
                _, key, value = line.split("#")
                # We don't know what order these will be in, so
                # we will just try to guess the type.
                data[key] = guess_type(key, value)
            except ValueError:
                pass
        return data

    def load_all_nodes(self):
        return self._run("load_all_nodes")

    def show_all_lines(self) -> List[str]:
        result = self._run("show_all_lines")
        if "ERROR" in result:
            raise RuntimeError(f"{result}")
        return result.split("\n")

    def show_effective_stack(self):
        return int(self._run("show_effective_stack").strip())

    def remove_line(self, line: str):
        line = [str(l) for l in line]
        return self._run("remove_line", " ".join(line))

    def add_line(self, line):
        line = [str(l) for l in line]
        return self._run("add_line", " ".join(line))

    def clear_lines(self):
        return self._run("clear_lines")

    def calc_ev(
        self, position: str | int, node
    ) -> Tuple[np.ndarray[float], np.ndarray[float]]:
        """
        EV of a given player in a given node for all hands.

        Numbers in the first item are EV, in the second item matchups.

        :position: "OOP" or "IP"
        :node: the node id (e.g., "r:0:c:c:7s:c")

        :return: a tuple of (evs, matchups), where each is a length 1326 tuple
            of floats
        """
        position = normalize_position(position)
        results = self._run("calc_ev", position, node)
        evs, matchups = results.split("\n")
        evs = np.array([float(ev) for ev in evs.split()])
        matchups = np.array([float(matchup) for matchup in matchups.split()])
        return evs, matchups

    def calc_ev_pp(self, position: str | int, node) -> str:
        """
        EV of a given player in a given node for all hands.

        Numbers in the first item are EV, in the second are matchups.

        :position: "OOP" or "IP"
        :node_id: the node id (e.g., "r:0:c:c:7s:c")

        :return: a human readable per-hand EV summary
        """
        position = normalize_position(position)
        results = self._run("calc_ev_pp", position, node)
        return tuple(results.split("\n"))

    def calc_matchups_line(self, node_id: str | Node) -> float:
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        result = self._run("calc_matchups_line", node_id)
        return float(result)

    def calc_eq(
        self, position: str | int
    ) -> Tuple[np.ndarray[float], np.ndarray[float]]:
        """
        Equities for a given player in all hands given the game state.
        NOTE: This is NOT for a given node. Instead, use `calc_eq_node`.

        Numbers in the first item are equities, numbers in the second are matchups.

        :position: "OOP" or "IP"

        :return: a tuple of (equities, matchups), where each is a length 1326
            tuple of floats
        """
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        position = normalize_position(position)
        results = self._run("calc_eq", position)
        eqs, matchups = results.split("\n")
        eqs = np.array([float(ev) for ev in eqs.split()])
        matchups = np.array([float(matchup) for matchup in matchups.split()])
        return eqs, matchups

    def calc_eq_pp(self, position: str | int, node_id: str | Node) -> str:
        """
        Equities for a given player in a given node for all hands.

        Numbers in the first item are EV, in the second are matchups.

        :position: "OOP" or "IP"
        :node_id: the node id (e.g., "r:0:c:c:7s:c")

        :return: a human readable per-hand equity summary
        """
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        position = normalize_position(position)
        results = self._run("calc_eq_pp", position, node_id)
        return tuple(results.split("\n"))

    def calc_eq_node(
        self, position: str | int, node_id: str | Node
    ) -> Tuple[np.ndarray[float], np.ndarray[float], float]:
        """
        Equity for given player assuming ranges in given node.

        Numbers in first item are equities, numbers in second are matchups, and
        third item is total equities

        :position: "OOP" or "IP"
        :node_id: the node id (e.g., "r:0:c:c:7s:c")
        """
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        position = normalize_position(position)
        results = self._run("calc_eq_node", position, node_id)
        try:
            eqs, matchups, total = results.split("\n")
        except ValueError:
            raise RuntimeError(f"Pio Error: calc_eq_node: {results}")
        eqs = np.array([float(ev) for ev in eqs.split()])
        matchups = np.array([float(matchup) for matchup in matchups.split()])
        total = float(total)
        return eqs, matchups, total

    def calc_eq_preflop(
        self, position: str | int
    ) -> Tuple[np.ndarray[float], np.ndarray[float], float]:
        """
        Preflop equity for given player assuming ranges in set_range command.

        Numbers in first item are equities, numbers in second are matchups, and
        third item is total equities

        :position: "OOP" or "IP"
        """
        position = normalize_position(position)
        results = self._run("calc_eq_preflop", position)
        try:
            eqs, matchups, total = results.split("\n")
        except ValueError:
            raise RuntimeError(f"Pio Error: calc_eq_preflop: {results}")
        eqs = np.array([float(ev) for ev in eqs.split()])
        matchups = np.array([float(matchup) for matchup in matchups.split()])
        total = float(total)
        return eqs, matchups, total

    def solve_partial(self, node_id: str | Node):
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        return self._run("solve_partial", node_id)

    def show_range(self, position: str | int, node_id: Optional[str | Node]) -> Range:
        """
        Show range in given node as a list of 1326 floats from 0.0 (not
        present) to 1.0 (full combo).  If only one argument is given then
        IP/OOPrange from solver state is shown (the one set by set_range).
        """
        position = normalize_position(position)
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        if node_id is None:
            range = self._run("show_range", position)
        else:
            range = self._run("show_range", position, node_id)
        if "ERROR" in range:
            print(f"Error in range at {position} {node_id}")
            print(f"{range}")
            return None
        return Range([float(freq) for freq in range.split()])

    def set_range(self, position: str | int, rng: str | List[float] | Range):
        if isinstance(rng, str):
            r = rng
        elif isinstance(rng, list):
            r = " ".join([str(x) for x in rng])
        elif isinstance(rng, Range):
            r = rng.pio_str()
        position = normalize_position(position)
        return self._run("set_range", position, r)

    def set_eff_stack(self, value: int):
        return self._run("set_eff_stack", str(value))

    def set_pot(self, oop: int, ip: int, start: int):
        return self._run("set_pot", str(oop), str(ip), str(start))

    def set_board(self, board: str):
        return self._run("set_board", "".join(board))

    def build_tree(self):
        return self._run("build_tree")

    def set_isomorphism(self, flop_trees: bool | int, turn_trees: bool | int):
        flop_trees = bool_or_int_to_int(flop_trees)
        turn_trees = bool_or_int_to_int(turn_trees)
        return self._run("set_isomorphism", str(flop_trees), str(turn_trees))

    def dump_tree(self, filename: str, save_type="no_rivers"):
        save_type = save_type.lower().replace("-", "_")
        if save_type in ("small", "no_rivers", None):
            save_type = "no_rivers"
        elif save_type in ("very_small", "no_turns"):
            save_type = "no_turns"
        elif save_type in ("normal", "full"):
            save_type = "full"
        if save_type not in ["no_turns", "no_rivers", "full"]:
            return self._run("dump_tree", filename, "no_rivers")
        if save_type == "full":
            return self._run("dump_tree", filename)
        return self._run("dump_tree", filename, save_type)

    def lock_node(self, node_id: str | Node):
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        response = self._run("lock_node", node_id)
        return response

    def unlock_node(self, node_id: str | Node):
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        response = self._run("unlock_node", node_id)
        return response

    def load_script(self, script_filepath: str):
        return self._run("load_script", script_filepath)

    def load_script_silent(self, script_filepath: str):
        return self._run("load_script_silent", script_filepath)

    def set_strategy(self, node_id: str | Node, values: List[float]):
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        values = [str(v) for v in values]
        response = self._run("set_strategy", node_id, *values)
        return response

    def show_strategy(self, node_id: str | Node) -> List[List[float]]:
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        strats = self._run("show_strategy", node_id).split("\n")
        return [[float(s) for s in strat.split()] for strat in strats]

    def calc_global_freq(self, node_id: str | Node) -> float:
        if isinstance(node_id, Node):
            node_id = node_id.node_id
        return float(self._run("calc_global_freq", node_id))

    def _parse_data(self, data, *name_to_parser):
        parsed_data = {}
        for i, data_line in enumerate(data.split("\n")):
            name = name_to_parser[i][0]
            parse_func = name_to_parser[i][1]
            parsed_data[name] = parse_func(data_line)
        return parsed_data

    def _run(self, *commands):
        if len(commands) == 0:
            return None
        command = commands[0]
        command_with_args = " ".join(commands)
        if self.store_script:
            self.commands.append(command_with_args)

        if self.debug:
            print(command_with_args)
        if self.log_file:
            self.log_file.write(f"[>] {command_with_args}\n")
            self.log_file.flush()

        if self.simulate:
            return
        self.process.stdin.write(command_with_args + "\n")
        end_string = f"{self.end_string}\n"
        lines = []

        trigger_word = None
        if command in _NO_OUTPUT_COMMANDS:
            # We need to use a trigger word to tell if we are done
            trigger_word = f"{command} ok!\n"

        if trigger_word:
            found_tw = False
            while True:
                lines.append(self.process.stdout.readline())
                if trigger_word in lines[-1]:
                    found_tw = True
                if found_tw and end_string in lines[-1]:
                    break

        else:
            while True:
                lines.append(self.process.stdout.readline())
                if end_string in lines[-1]:
                    break

        output = "".join(lines)

        if self.debug:
            print(output)
        if self.log_file:
            self.log_file.write(f"[<] {output}\n")
            self.log_file.flush()

        return output.replace("END\n", "").strip()

    def _get_solver_output(self, trigger_word, quiet=False):
        end_string = f"{self.end_string}\n"
        lines = []
        if trigger_word:
            while True:
                line = self.process.stdout.readline()
                if self.debug:
                    print(f"Found line: {line}", end="")
                lines.append(line)
                if trigger_word in lines[-1]:
                    print("Found Trigger word")
                    break

        else:
            while True:
                line = self.process.stdout.readline()
                if self.debug:
                    print(f"Found line: {line}", end="")
                lines.append(line)
                if end_string in lines[-1]:
                    break
        output = "".join(lines)

        if self.debug:
            print(output)
        elif not quiet:
            print(output)

        if self.log_file:
            self.log_file.write(f"[<] {output}\n")
            self.log_file.flush()

        return output.replace("END\n", "").strip()

    def __del__(self):
        if self.log_file:
            self.log_file.close()
        if self.process:
            self.process.kill()
        if self.store_script:
            with open("script.txt", "w") as f:
                f.write("\n".join(self.commands))


def typed_list(data, t):
    return [t(a) for a in data.split()]


def first_int(to_parse):
    return int(to_parse.split(" ")[0])


def guess_type(key, data_string):
    if "Config" in key and "Size" in key:
        values = data_string.split(",")
        values = [try_value_as_int(s) for v in values for s in v.split(" ") if s]
        return values
    if "Range" in key:
        return data_string.split(",")
    if "Board" == key:
        return data_string.split(" ")
    return try_value_as_literal(data_string)


def info_range_to_pio_range(hand_order, info_range):
    hand_class_to_weight = {}
    for blob in info_range:
        if ":" not in blob:
            hand_class = blob
            weight = 1
        else:
            hand_class, weight = blob.split(":")
        hand_class_to_weight[hand_class] = weight
    weights = []
    for specific_hand in hand_order:
        added = False
        for hand_class, weight in hand_class_to_weight.items():
            if is_member(specific_hand, hand_class):
                weights.append(weight)
                added = True
                break
        if not added:
            weights.append(0)
    return weights


def is_member(hand, hand_class):
    if len(hand_class) == 2:
        if hand_class[0] == hand_class[1]:
            # JsJh, JJ
            return hand[0] == hand[2] == hand_class[0]
        else:
            # AhKs, AK
            return (hand[0] == hand_class[0] and hand[2] == hand_class[1]) or (
                hand[0] == hand_class[1] and hand[2] == hand_class[0]
            )
    assert len(hand_class) == 3
    ranks_match = (hand[0] == hand_class[0] and hand[2] == hand_class[1]) or (
        hand[0] == hand_class[1] and hand[2] == hand_class[0]
    )
    if hand_class[2] == "s":
        return ranks_match and hand[1] == hand[3]
    else:
        assert hand_class[2] == "o"
        return ranks_match and hand[1] != hand[3]


_NO_OUTPUT_COMMANDS = [
    "is_ready",
    "set_end_string",
    "load_tree",
    "dump_tree",
    "go",
    "stop",
    "wait_for_solver",
    "take_a_break",
    "set_threads",
    "set_info_freq",
    "set_accuracy",
    "set_recalc_accuracy",
    "set_always_recalc",
    "set_isomorphism",
    "set_first_iteration_player",
    "add_preflop_line",
    "remove_preflop_line",
    "clear_preflop_lines",
    "build_preflop_tree",
    "add_to_subset",
    "reset_subset",
    "recover_subset",
    "add_schematic_tree",
    "add_all_flops",
    "set_algorithm",
    "small_strats",
    "add_info_line",
    "reset_tree_info",
    "solve_partial",
    "solve_all_splits",
    "eliminate_path",
    "lock_node",
    "unlock_node",
    "combo_lock_node",
    "set_equal_strats",
    "set_mes",
    "free_tree",
]


def bool_or_int_to_int(v: int | bool):
    if v == True:
        return 1
    if v == False:
        return 0
    return v
