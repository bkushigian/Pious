from os import path as osp

import importlib.resources


def get_test_tree(tree="Kh7h2c.cfr"):
    trees_path = importlib.resources.files("pious.pio.resources.trees")
    cfr_path = osp.join(trees_path, tree)
    return cfr_path


def get_database_root():
    resources_path = importlib.resources.files("pious.pio.resources")
    return osp.join(resources_path, "database")


def get_aggregation_root():
    resources_path = importlib.resources.files("pious.pio.resources")
    return osp.join(resources_path, "aggregation", "Root")


def get_aggregation_dir_node(*actions):
    root = get_aggregation_root()
    return osp.join(root, *actions)
