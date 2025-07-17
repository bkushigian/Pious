from pious.hands import Hand
from pious.pio.aggregate import SpotData
import pytest
import os
from os import path as osp
import importlib.resources
from pious.pio import make_solver, Line
from pious.pio.resources import get_test_tree
from pious.pio.aggregate import aggregate_single_file


def test_hands_df_on_toak_board():
    pass


cfr_db_path = importlib.resources.files("pious.pio.resources.database")
cfr_path = cfr_db_path / "2c2s2d.cfr"


# TODO: This is in the wrong test file
@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_blocker_effects():
    s = make_solver()
    s.load_tree(str(cfr_path))
    spot = SpotData(s, "r:0")
    df = spot.hands_df()
    AsAh = df[df["hand"] == "AsAh"]
    assert AsAh.iloc[0]["hand_type"] == Hand.FULL_HOUSE

    _5c4c = df[df["hand"] == "5c4c"]
    assert _5c4c.iloc[0]["hand_type"] == Hand.HIGH_CARD


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_single_file_default_config():
    t = get_test_tree()
    s = make_solver()
    s.load_tree(t)
    lines = [Line(l) for l in ["r:0", "r:0:c", "r:0:b300"]]
    l0, l1, l2 = lines

    ag = aggregate_single_file(t, lines)
    ag = {l.line_str: df for l, df in ag.items()}
    ag0 = ag[l0.line_str].iloc[0]  # Get first row as Series
    ag1 = ag[l1.line_str].iloc[0]  # Get first row as Series
    ag2 = ag[l2.line_str].iloc[0]

    assert ag0["Flop"] == "Kh7h2c"
    assert ag0["OOP EV"] == pytest.approx(165.602843)
    assert ag0["IP EV"] == pytest.approx(132.897156)
    assert ag0["OOP Equity"] == pytest.approx(0.528665)
    assert ag0["IP Equity"] == pytest.approx(0.471334)
    assert ag0["Check Freq"] == pytest.approx(58.891395)
    assert ag0["Bet 300 Freq"] == pytest.approx(41.108604)
    assert ag0["Bet 850 Freq"] == pytest.approx(0.0)

    assert ag1["Flop"] == "Kh7h2c"
    assert ag1["OOP EV"] == pytest.approx(141.650326)
    assert ag1["IP EV"] == pytest.approx(156.849696)
    assert ag1["OOP Equity"] == pytest.approx(0.517879)
    assert ag1["IP Equity"] == pytest.approx(0.482119)
    assert ag1["Check Freq"] == pytest.approx(89.966564)
    assert ag1["Bet 300 Freq"] == pytest.approx(10.033435)
    assert ag1["Bet 850 Freq"] == pytest.approx(0.0)

    assert ag2["Flop"] == "Kh7h2c"
    assert ag2["OOP EV"] == pytest.approx(500.203785)
    assert ag2["IP EV"] == pytest.approx(98.296226)
    assert ag2["OOP Equity"] == pytest.approx(0.544246)
    assert ag2["IP Equity"] == pytest.approx(0.455754, rel=1e-5)
    assert ag2["Fold Freq"] == pytest.approx(56.58156)
    assert ag2["Call Freq"] == pytest.approx(25.641076)
    assert ag2["Raise 850 Freq"] == pytest.approx(17.777363)
