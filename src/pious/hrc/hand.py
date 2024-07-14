"""
An exported HRC Hand
"""

from os import path as osp
from os import listdir
import json


class Solve:
    def __init__(self, hand_export_dir):
        self.hand_export_dir = hand_export_dir
        self.settings_json_path = osp.join(self.hand_export_dir, "settings.json")
        with open(self.settings_json_path) as f:
            contents = f.read()
        self.settings = SolveSettings(json.loads(contents))
        self.nodes = []
        self.nodes_path = osp.join(hand_export_dir, "nodes")
        for node_file_json in listdir(self.nodes_path):
            if not node_file_json.endswith(".json"):
                print(
                    "Warning: unrecognized file",
                    node_file_json,
                    "in nodes path:",
                    self.nodes_path,
                )
                continue
            node_file_json_path = osp.join(self.nodes_path, node_file_json)
            node = HRCNode(node_file_json_path)
            self.nodes.append(node)


class SolveSettings:
    def __init__(self, settings):
        self._settings_json = settings
        self.hand_data = SolveData(settings["handdata"])
        self.tree_config = TreeConfig(settings["treeconfig"])
        self.engine = Engine(settings["engine"])
        self.eq_model = EqModel(settings["eqmodel"])


class SolveData:
    def __init__(self, d):
        self._hand_data_json = d
        self.stacks = d["stacks"]
        self.blinds = d["blinds"]
        self.skip_sb = d["skipSb"]
        self.moving_bu = d["movingBu"]
        self.ante_type = d["anteType"]


class TreeConfig:
    def __init__(self, d):
        self._tree_config_json = d
        self.mode = d["mode"]


class Engine:
    def __init__(self, d):
        self._engine_json = d
        self.type = d["type"]
        self.max_active = d["maxactive"]
        self.configuration = EngineConfiguration(d["configuration"])


class EngineConfiguration:
    def __init__(self, d):
        self._engine_configuration_json = d
        abstractions = d["abstractions"]
        self.preflop_abstractions = abstractions[0]["buckets"]
        self.flop_abstractions = abstractions[1]["buckets"]
        self.turn_abstractions = abstractions[2]["buckets"]
        self.river_abstractions = abstractions[3]["buckets"]


class EqModel:
    def __init__(self, d):
        self._eq_model_json = d
        self.rake_cap = d["rakecap"]
        self.rake_pct = d["rakepct"]
        self.id = d["id"]
        self.nfnd = d["nfnd"]
        self.raked = d["raked"]


class HRCNode:
    def __init__(self, node_json_file):
        self.filename = node_json_file
        self.id = int(osp.basename(node_json_file).strip(".json"))
        with open(node_json_file) as f:
            self._node_json = json.loads(f.read())

        d = self._node_json
        try:
            self.player = d["player"]
            self.street = d["street"]
            self.children = d["children"]
            self.sequence = ActionSequence(d["sequence"])
        except KeyError as e:
            print(d)
            print(e)
            print(node_json_file)
        self.actions = [Action(a) for a in d["actions"]]
        self.hands = {h: HandData(h, d["hands"][h]) for h in d["hands"]}

    def __str__(self):
        return f"Node(id={self.id})"

    def __repr__(self):
        return str(self)


class ActionSequence:
    """
    The sequence of player actions that led to this node.
    """

    def __init__(self, l):
        self._action_sequence_json = l
        self.player_actions = [PlayerAction(d) for d in l]

    def __str__(self):
        return f"ActionSequence[{', '.join(str(a) for a in self.player_actions)}]"


class Action:
    action_map = {"R": "Raise", "F": "Fold", "C": "Call"}

    def __init__(self, d):
        self.type = d["type"]
        self.amount = d["amount"]

    def __str__(self):
        a = Action.action_map[self.type]
        if self.amount > 0:
            return f"Action[{a}({self.amount})]"
        else:
            return f"Action[{a}]"

    def __repr__(self):
        return str(self)


class PlayerAction:
    """
    Actions that a player may take
    """

    def __init__(self, d):
        self.player = d["player"]
        self.action = Action(d)

    def __str__(self):
        return f"PlayerAction(player={self.player},action={self.action})"

    def __repr__(self):
        return str(self)


class HandData:
    def __init__(self, hand, d):
        self._hand_data_json = d
        self.hand = hand
        self.weight = d["weight"]
        self.played = tuple(d["played"])
        self.evs = tuple(d["evs"])
