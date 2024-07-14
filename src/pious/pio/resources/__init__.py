from os import path as osp

import importlib.resources


def get_test_tree(tree="Kh7h2c.cfr"):
    trees_path = importlib.resources.files("pious.pio.resources.trees")
    cfr_path = osp.join(trees_path, tree)
    return cfr_path
