import pytest
import os
from pious.hands import Hand
from pious.pio.aggregate import SpotData
from pious.pio.database import CFRDatabase
from pious.pio.blockers import compute_single_card_blocker_effects
from pious.pio.util import make_solver
from pious.pio.resources import get_test_database


db: CFRDatabase = get_test_database()


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_spot_data_hands():
    s = make_solver()
    cfr_path = db["2h2c2d"]
    s.load_tree(str(cfr_path))
    spot = SpotData(s, "r:0")
    df = spot.hands_df()
    AsAh = df[df["hand"] == "AsAh"]
    assert AsAh.iloc[0]["hand_type"] == Hand.FULL_HOUSE

    _5c4c = df[df["hand"] == "5c4c"]
    assert _5c4c.iloc[0]["hand_type"] == Hand.HIGH_CARD
