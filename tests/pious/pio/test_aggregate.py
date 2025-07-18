from pious.hands import Hand
from pious.pio.aggregate import SpotData, AggregationConfig
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
    assert ag0["Check Freq"] == pytest.approx(59.09, rel=1e-2)
    assert ag0["Bet 300 Freq"] == pytest.approx(40.91, rel=1e-2)
    assert ag0["Bet 850 Freq"] == pytest.approx(0.0)

    assert ag1["Flop"] == "Kh7h2c"
    assert ag1["OOP EV"] == pytest.approx(141.650326)
    assert ag1["IP EV"] == pytest.approx(156.849696)
    assert ag1["OOP Equity"] == pytest.approx(0.517879)
    assert ag1["IP Equity"] == pytest.approx(0.482119)
    assert ag1["Check Freq"] == pytest.approx(90.04, rel=1e-2)
    assert ag1["Bet 300 Freq"] == pytest.approx(9.96, rel=1e-2)
    assert ag1["Bet 850 Freq"] == pytest.approx(0.0)

    assert ag2["Flop"] == "Kh7h2c"
    assert ag2["OOP EV"] == pytest.approx(500.203785)
    assert ag2["IP EV"] == pytest.approx(98.296226)
    assert ag2["OOP Equity"] == pytest.approx(0.544246)
    assert ag2["IP Equity"] == pytest.approx(0.455754, rel=1e-5)
    assert ag2["Fold Freq"] == pytest.approx(57.67, rel=1e-2)
    assert ag2["Call Freq"] == pytest.approx(25.15, rel=1e-2)
    assert ag2["Raise 850 Freq"] == pytest.approx(17.18, rel=1e-2)


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_single_file_custom_config_01():
    t = get_test_tree()
    s = make_solver()
    s.load_tree(t)
    config = AggregationConfig(action_evs=True, global_freq=True)
    lines = [Line(l) for l in ["r:0", "r:0:c", "r:0:b300"]]
    ag = aggregate_single_file(t, lines, conf=config)
    l0, l1, l2 = lines

    ag = {l.line_str: df for l, df in ag.items()}
    ag0 = ag[l0.line_str].iloc[0]  # Get first row as Series
    ag1 = ag[l1.line_str].iloc[0]  # Get first row as Series
    ag2 = ag[l2.line_str].iloc[0]

    assert ag0["Flop"] == "Kh7h2c"
    assert ag0["Global Freq"] == 1.0
    assert ag0["OOP EV"] == pytest.approx(165.60, rel=1e-2)
    assert ag0["IP EV"] == pytest.approx(132.90, rel=1e-2)
    assert ag0["OOP Equity"] == pytest.approx(0.52867, rel=1e-5)
    assert ag0["IP Equity"] == pytest.approx(0.47133, rel=1e-5)
    assert ag0["Check Freq"] == pytest.approx(59.09, rel=1e-2)
    assert ag0["Bet 300 Freq"] == pytest.approx(40.91, rel=1e-2)
    assert ag0["Bet 850 Freq"] == pytest.approx(0.0)
    assert ag0["Check EV"] == pytest.approx(83.705258)
    assert ag0["Bet 300 EV"] == pytest.approx(81.897584)
    assert ag0["Bet 850 EV"] == pytest.approx(0.0)

    # Flop                Kh7h2c
    # Global Freq       0.590929
    # OOP EV          141.650326
    # IP EV           156.849696
    # OOP Equity        0.517879
    # IP Equity         0.482119
    # Check Freq       89.966564
    # Bet 300 Freq     10.033435
    # Bet 850 Freq           0.0
    # Check EV        134.149602
    # Bet 300 EV       22.700091
    # Bet 850 EV             0.0

    # Flop                  Kh7h2c
    # Global Freq         0.409071
    # OOP EV            500.203785
    # IP EV              98.296226
    # OOP Equity          0.544246
    # IP Equity           0.455754
    # Fold Freq           56.58156
    # Call Freq          25.641076
    # Raise 850 Freq     17.777363
    # Fold EV             0.000025
    # Call EV            60.416299
    # Raise 850 EV       37.879902
    # Name: 0, dtype: object
