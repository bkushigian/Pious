from pious.pio.blockers import compute_single_card_blocker_effects
from pious.pio.util import make_solver

s = make_solver()
s.load_tree(r"F:\Database\SimpleTree\SRP\Range b25\BTNvBB\5c4d3c.cfr")


def test_blocker_effects():
    effects = compute_single_card_blocker_effects(s, "r:0:c")
    return effects
