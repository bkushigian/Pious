"""
This file is taken from https://github.com/weston/pyosolver. I've modified it to
suit my needs.
"""

import subprocess
import os
from decimal import Decimal, InvalidOperation
from functools import partial
from uuid import uuid4
import time


class PYOSolver(object):
    def __init__(
        self,
        path,
        executable_name,
        debug=False,
        log_file=None,
        store_script=False,
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

    def load_tree(self, cfr_file_path):
        self.cfr_file_path = cfr_file_path
        self._run("load_tree", cfr_file_path)
        root_node_info = self.show_node("r:0")
        if self.debug:
            print(f"root_node_info: {root_node_info}\n")
        self._run("set_isomorphism", "1 0")
        self.set_pot(*root_node_info["pot"])
        self.clear_lines()

    def show_node(self, node_id):
        self._run("show_node", node_id)
        return self._parse_data(
            self._run("show_node", node_id),
            ("nodeID", str),
            ("NODE_TYPE", str),
            ("board", partial(typed_list, t=str)),
            ("pot", partial(typed_list, t=int)),
            ("children_no", first_int),
            ("flags", str),
        )

    def show_children(self, node_id):
        data = self._run("show_children", node_id).split("\n")
        if len(data) == 1 and data[0].startswith("ERROR"):
            return []
        i = 0
        nodes = []
        data = [d for d in data if d != ""]
        while i < len(data):
            assert "child" in data[i], print(f"Invalid data: {data[i]}")
            # Can add more data here (same format as show_node)
            nodes.append(
                {
                    "nodeID": data[i + 1],
                    "last_action": data[i + 1].split(":")[-1],
                }
            )
            i += 8
        return nodes

    def show_hand_order(self):
        return self._run("show_hand_order").split(" ")

    def go(self):
        return self._run("go")

    def wait_for_solver(self):
        return self._run("wait_for_solver")

    def rebuild_forgotten_streets(self):
        return self._run("rebuild_forgotten_streets")

    def show_tree_info(self):
        data = {}
        self._run("show_tree_info")
        for line in self._run("show_tree_info").split("\n"):
            _, key, value = line.split("#")
            # We don't know what order these will be in, so
            # we will just try to guess the type.
            data[key] = guess_type(key, value)
        return data

    def show_all_lines(self):
        return self._run("show_all_lines").split("\n")

    def show_effective_stack(self):
        return int(self._run("show_effective_stack").strip())

    def remove_line(self, line):
        line = [str(l) for l in line]
        return self._run("remove_line", " ".join(line))

    def add_line(self, line):
        line = [str(l) for l in line]
        return self._run("add_line", " ".join(line))

    def clear_lines(self):
        return self._run("clear_lines")

    def calc_ev(self, position, node):
        results = self._run("calc_ev_pp", position, node)
        for r in results.split("\n"):
            if "EV: " in r:
                return float(r.split(": ")[1])
        return None

    def solve_partial(self, node_id):
        return self._run("solve_partial", node_id)

    def show_range(self, position, node_id):
        return [float(a) for a in self._run("show_range", position, node_id).split()]

    def set_range(self, position, *values):
        values = [str(a) for a in values]
        return self._run("set_range", position, *values)

    def set_eff_stack(self, value):
        return self._run("set_eff_stack", str(value))

    def set_pot(self, oop, ip, start):
        return self._run("set_pot", str(oop), str(ip), str(start))

    def set_board(self, board):
        return self._run("set_board", "".join(board))

    def build_tree(self):
        return self._run("build_tree")

    def dump_tree(self, filename):
        return self._run("dump_tree", filename)

    def lock_node(self, node_id):
        return self._run("lock_node", node_id)

    def set_strategy(self, node_id, *values):
        values = [str(v) for v in values]
        return self._run("set_strategy", node_id, *values)

    def show_strategy(self, node_id):
        strats = self._run("show_strategy", node_id).split("\n")
        return [[float(s) for s in strat.split()] for strat in strats]

    def _parse_data(self, data, *name_to_parser):
        parsed_data = {}
        for i, data_line in enumerate(data.split("\n")):
            name = name_to_parser[i][0]
            parse_func = name_to_parser[i][1]
            parsed_data[name] = parse_func(data_line)
        return parsed_data

    def _run(self, *commands):
        command = " ".join(commands)
        if self.store_script:
            self.commands.append(command)

        if self.debug:
            print(command)
        if self.log_file:
            self.log_file.write(f"[>] {command}\n")
            self.log_file.flush()

        self.process.stdin.write(" ".join(commands) + "\n")
        no_output_commands = [
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
        trigger_word = f"{self.end_string}\n"
        lines = []

        while True:
            lines.append(self.process.stdout.readline())
            if trigger_word in lines[-1]:
                break

        output = "".join(lines)

        if self.debug:
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
        if data_string.find(","):
            try:
                return [int(a) for a in data_string.split(",")]
            # Case where sizings are expressed as allin 3x or 2e
            except ValueError:
                return data_string.split(",")
        else:
            try:
                return [int(a) for a in data_string.split(" ")]
            except ValueError:
                return data_string.split(" ")
    if "Range" in key:
        return data_string.split(",")
    if "Board" == key:
        return data_string.split(" ")
    return try_value_as_literal(data_string)


def try_value_as_literal(data_string):
    try:
        return bool(data_string)
    except ValueError:
        pass
    try:
        return int(data_string)
    except ValueError:
        pass
    try:
        return float(data_string)
    except ValueError:
        pass
    return data_string


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
