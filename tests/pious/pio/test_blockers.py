import pytest
import os
from pious.hands import Hand
from pious.pio.aggregate import SpotData
from pious.pio.blockers import compute_single_card_blocker_effects
from pious.pio.util import make_solver
import importlib.resources

cfr_db_path = importlib.resources.files("pious.pio.resources.database")
cfr_path = cfr_db_path / "2c2s2d.cfr"


# TODO: This is not a good test!
@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_blocker_effects():
    s = make_solver()
    s.load_tree(str(cfr_path))

    effects = compute_single_card_blocker_effects(s, "r:0:c")
    print(effects)
