from os import path as osp
import importlib.resources

from pious.pio.tree_building import (
    parse_postflop_tree_build_config,
)

trees_path = importlib.resources.files("pious.pio.resources.trees")
cfr_path = osp.join(trees_path, "Kh7h2c.cfr")
tree_building_path = importlib.resources.files("pious.pio.resources.tree_building")


def test_parse_postflop_tree_build_config():
    build_conf = osp.join(tree_building_path, "25bbHU-2sizes.txt")
    config = parse_postflop_tree_build_config(build_conf)
    assert config is not None
