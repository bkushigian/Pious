from pious.hands import Hand
from pious.pio.aggregate import SpotData
import pytest
import os
from os import path as osp
import importlib.resources
from pious.pio import make_solver


def test_hands_df_on_toak_board():
    pass


cfr_db_path = importlib.resources.files("pious.pio.resources.database")
cfr_path = cfr_db_path / "2c2s2d.cfr"


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_blocker_effects():
    s = make_solver()
    s.load_tree(str(cfr_path))
    spot = SpotData(s, "r:0")
    df = spot.hands_df()
    AsAh = df[df["hand"] == "AsAh"]
    assert AsAh.iloc[0]["hand_type"] == Hand.FULL_HOUSE

    print(df)
    _5c4c = df[df["hand"] == "5c4c"]
    print(_5c4c["hand_type"])
    assert _5c4c.iloc[0]["hand_type"] == Hand.HIGH_CARD
