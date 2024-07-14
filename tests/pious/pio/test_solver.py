from pious.pio.util import make_solver
from pious.pio.solver import Node
from os import path as osp
import importlib.resources


cfr_path = osp.join(
    importlib.resources.files("pious.pio.resources.trees"), "Kh7h2c.cfr"
)


def test_make_solver():
    solver = make_solver()
    assert solver.is_ready()


def test_solver_load_tree():
    solver = make_solver()
    solver.load_tree(cfr_path)
    assert solver.is_ready()


def test_show_node():
    solver = make_solver()
    solver.load_tree(cfr_path)
    n = solver.show_node("r:0")
    assert n.pot == (0, 0, 300)
    assert n.node_id == "r:0"
    assert n.node_type == "OOP_DEC"

    n = solver.show_node("r:0:b850")
    assert isinstance(n, Node)
    assert n.node_id == "r:0:b850"
    assert n.node_type == "IP_DEC"
    assert n.pot == (850, 0, 300)


def test_show_children():
    solver = make_solver()
    solver.load_tree(cfr_path)
    children = solver.show_children("r:0")
    assert len(children) == 3


def test_show_children_actions():
    solver = make_solver()
    solver.load_tree(cfr_path)
    children_actions = solver.show_children_actions("r:0")
    assert children_actions == ["b850", "b300", "c"]


def test_show_hand_order():
    solver = make_solver()
    solver.load_tree(cfr_path)
    assert solver.show_hand_order() is not None


def test_show_tree_info():
    solver = make_solver()
    solver.load_tree(cfr_path)
    tree_info = solver.show_tree_info()

    assert tree_info["Rake.Enabled"]
    assert tree_info["Rake.Fraction"]
    assert tree_info["Rake.Cap"]
    assert tree_info["Board"] == ["Kh", "7h", "2c"]
    assert tree_info["Pot"]
    assert tree_info["EffectiveStacks"]
    assert tree_info["AllinThreshold"]
    assert tree_info["AddAllinOnlyIfLessThanThisTimesThePot"]

    assert tree_info["FlopConfig.BetSize"] == [100]
    assert tree_info["FlopConfig.RaiseSize"] == [40, "ai"]
    assert tree_info["FlopConfig.AddAllin"]
    assert tree_info["TurnConfig.BetSize"] == [100]
    assert tree_info["TurnConfig.RaiseSize"] == [40, "ai"]
    assert tree_info["TurnConfig.DonkBetSize"] == [100]
    assert tree_info["TurnConfig.AddAllin"]
    assert tree_info["RiverConfig.BetSize"] == [100]
    assert tree_info["RiverConfig.RaiseSize"] == [40, "ai"]
    assert tree_info["RiverConfig.DonkBetSize"] == [100]
    assert tree_info["RiverConfig.AddAllin"]

    assert tree_info["FlopConfigIP.BetSize"] == [100]
    assert tree_info["FlopConfigIP.RaiseSize"] == [40, "ai"]
    assert tree_info["FlopConfigIP.AddAllin"]
    assert tree_info["TurnConfigIP.BetSize"] == [100]
    assert tree_info["TurnConfigIP.RaiseSize"] == [40, "ai"]
    assert tree_info["TurnConfigIP.AddAllin"]
    assert tree_info["RiverConfigIP.BetSize"] == [100]
    assert tree_info["RiverConfigIP.RaiseSize"] == [40, "ai"]
    assert tree_info["RiverConfigIP.AddAllin"]

    range_oop = tree_info["Range0"]
    assert "AA" in range_oop
    assert "KK" in range_oop
    assert "QQ" in range_oop
    assert "JJ" in range_oop
    assert "TT" in range_oop
    assert "99:0.60799998" in range_oop


def test_rebuild_forgotten_streets():
    solver = make_solver()
    solver.load_tree(cfr_path)
    solver.rebuild_forgotten_streets()
    assert solver.is_ready()
