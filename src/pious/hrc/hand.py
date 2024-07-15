"""
An exported HRC Hand
"""

from os import path as osp
from os import listdir
import json


class HRCSim:
    def __init__(self, hand_export_dir):
        self.hand_export_dir = hand_export_dir
        self.settings_json_path = osp.join(self.hand_export_dir, "settings.json")
        with open(self.settings_json_path) as f:
            contents = f.read()
        self.settings = SolveSettings(json.loads(contents))
        self.nodes = []
        self.nodes_path = osp.join(hand_export_dir, "nodes")
        self.node_cache = NodeCache(self.nodes_path)
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
            node = self.node_cache[node_file_json_path]
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


class NodeCache:
    def __init__(self, nodes_path):
        self.nodes_path = nodes_path
        self.cache = {}

    def __getitem__(self, item):
        # Canonicalize the item into a full node path
        node_path = None
        if isinstance(item, int):
            item = osp.abspath(osp.join(self.nodes_path, f"{item}.json"))
        if isinstance(item, str):
            if (
                item.startswith(self.nodes_path)
                and item.endswith(".json")
                and osp.exists(item)
            ):
                node_path = osp.abspath(item)
            elif item.endswith(".json") and osp.exists(osp.join(self.nodes_path, item)):
                node_path = osp.abspath(osp.join(self.nodes_path, item))
            else:
                raise KeyError(f"No such node {item}")
        if node_path not in self.cache:
            self.cache[node_path] = HRCNode(node_path, self)
        return self.cache[node_path]


class HRCNode:
    def __init__(self, node_json_file, node_cache):
        self.node_cache = node_cache
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
        self.actions = tuple([Action(a) for a in d["actions"]])
        self.hands = {h: HandData(h, d["hands"][h]) for h in d["hands"]}

    def get_actions(self):
        return self.actions

    def get_hands(self):
        return self.hands

    def take_action(self, action) -> "HRCNode":
        a = None
        if isinstance(action, int):
            a: Action = self.get_actions()[action]
        else:
            raise RuntimeError("Can only take integer actions")
        if a.next_id is None:
            return None
        return self.node_cache[a.next_id]

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
        self.player_actions = [PreviousAction(d) for d in l]

    def __str__(self):
        return f"ActionSequence[{', '.join(str(a) for a in self.player_actions)}]"

    def __repr__(self):
        return str(self)


class Action:
    action_map = {"R": "Raise", "F": "Fold", "C": "Call"}

    def __init__(self, d):
        self.type = d["type"]
        self.amount = d["amount"]
        self.next_id = d.get("node", None)

    def __str__(self):
        a = Action.action_map[self.type]
        if self.amount > 0:
            return f"Action[{a}({self.amount})]"
        else:
            return f"Action[{a}]"

    def __repr__(self):
        return str(self)


class PreviousAction:
    """
    A previous action taken by a player in an action sequence
    """

    def __init__(self, d):
        self.player = d["player"]
        self.type = d["type"]
        self.amount = d["amount"]

    def __str__(self):
        return f"PlayerAction(player={self.player},action={self.type} {self.amount})"

    def __repr__(self):
        return str(self)


class HandData:
    def __init__(self, hand, d):
        self._hand_data_json = d
        self.hand = hand
        self.weight = d["weight"]
        self.played = tuple(d["played"])
        self.evs = tuple(d["evs"])
