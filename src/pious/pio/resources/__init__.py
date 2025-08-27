from os import path as osp

import importlib.resources
from pathlib import Path
from ..database import CFRDatabase


def get_test_tree(tree="Kh7h2c.cfr"):
    trees_path = importlib.resources.files("pious.pio.resources.trees")
    cfr_path = osp.join(trees_path, tree)
    return cfr_path


def get_database_root():
    resources_path = importlib.resources.files("pious.pio.resources")
    return osp.join(resources_path, "database")


def get_database_files():
    db_root = get_database_root()
    return [f for f in osp.listdir(db_root) if f.endswith(".cfr")]


def get_test_database(pio_viewer_location: str | Path | None = None) -> CFRDatabase:
    """
    Create a CFRDatabase instances with the test database. Optionally, specify
    the location of the PioViewer executable (default is
    C:\\PioSolver\\PioViewer3.exe), to allow the opening of files in the viewer.
    """
    return CFRDatabase(get_database_root(), pio_viewer_location=pio_viewer_location)


def get_aggregation_root():
    resources_path = importlib.resources.files("pious.pio.resources")
    return osp.join(resources_path, "aggregation", "Root")


def get_aggregation_dir_node(*actions):
    root = get_aggregation_root()
    return osp.join(root, *actions)
