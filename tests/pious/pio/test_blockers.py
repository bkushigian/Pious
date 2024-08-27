import pytest
import os
from pious.pio.blockers import compute_single_card_blocker_effects
from pious.pio.util import make_solver


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_blocker_effects():
    s = make_solver()
    s.load_tree(r"F:\Database\SimpleTree\SRP\Range b25\BTNvBB\5c4d3c.cfr")

    effects = compute_single_card_blocker_effects(s, "r:0:c")
    print(effects)
