import pytest
import os
from pious.pio.blockers import compute_single_card_blocker_effects
from pious.pio.util import make_solver
import importlib.resources

cfr_db_path = importlib.resources.files("pious.pio.resources.database")
cfr_path = cfr_db_path / "2c2s2d.cfr"


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_blocker_effects():
    s = make_solver()
    s.load_tree(str(cfr_path))

    effects = compute_single_card_blocker_effects(s, "r:0:c")
    print(effects)
