from pious.hands import Hand
import pytest
import os
import importlib.resources
from pious.pio import make_solver, Line
from pious.pio import aggregate as ag
from pious.pio.resources import get_test_tree, get_database_root
from pious.pio.aggregate import SpotData, AggregationConfig, aggregate_single_file, LinesToAggregate
import pious._executables.aggregate as agg_exec
import numpy as np


def close_enough(actual, expected, tolerance, absolute_tolerance=True):
    if absolute_tolerance:
        return abs(actual - expected) < tolerance
    else:
        return abs(actual - expected) / expected * 100 < tolerance

@pytest.fixture
def solver():
    return make_solver(debug=False)

@pytest.fixture
def test_tree():
    return get_test_tree()

def solver_with_test_tree(solver, test_tree):
    solver.load_tree(test_tree)
    return solver

@pytest.fixture
def database_very_small_path():
    new_set_path = importlib.resources.files("pious.pio.resources.database.very_small")
    return new_set_path

@pytest.fixture
def file_path_cfrQJ4c(database_very_small_path):
    cfr_path = database_very_small_path.joinpath(r"QsJs4h.cfr")
    return str(cfr_path)

@pytest.fixture
def cfrQJ4(solver,file_path_cfrQJ4c):
    solver.load_tree(file_path_cfrQJ4c)
    return solver

@pytest.fixture
def QJ4_c_b18_b54(cfrQJ4):
    return ag.SpotData(cfrQJ4, "r:0:c:b18:b54")

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
    assert ag0["IP EV"] == pytest.approx(132.897156, rel=1e-2)
    assert ag0["OOP Equity"] == pytest.approx(0.528665)
    assert ag0["IP Equity"] == pytest.approx(0.471334)
    assert ag0["Check Freq"] == pytest.approx(59.09, rel=1e-2)
    assert ag0["Bet 300 Freq"] == pytest.approx(40.91, rel=1e-2)
    assert ag0["Bet 850 Freq"] == pytest.approx(0.0)

    assert ag1["Flop"] == "Kh7h2c"
    assert ag1["OOP EV"] == pytest.approx(141.650326)
    assert ag1["IP EV"] == pytest.approx(156.849696)
    assert ag1["OOP Equity"] == pytest.approx(0.517879, rel=1e-5)
    assert ag1["IP Equity"] == pytest.approx(0.482119, rel=1e-5)
    assert ag1["Check Freq"] == pytest.approx(90.04, rel=1e-2)
    assert ag1["Bet 300 Freq"] == pytest.approx(9.96, rel=1e-2)
    assert ag1["Bet 850 Freq"] == pytest.approx(0.0, rel=1e-2)

    assert ag2["Flop"] == "Kh7h2c"
    assert ag2["OOP EV"] == pytest.approx(500.20, rel=1e-2)
    assert ag2["IP EV"] == pytest.approx(98.30, rel=1e-2)
    assert ag2["OOP Equity"] == pytest.approx(0.54425, rel=1e-5)
    assert ag2["IP Equity"] == pytest.approx(0.45575, rel=1e-5)
    assert ag2["Fold Freq"] == pytest.approx(57.67, rel=1e-2)
    assert ag2["Call Freq"] == pytest.approx(25.15, rel=1e-2)
    assert ag2["Raise 850 Freq"] == pytest.approx(17.18, rel=1e-2)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_single_file_custom_config_01(solver, test_tree):
    t = get_test_tree()
    s = make_solver()
    s.load_tree(t)
    lines = [Line(l) for l in ["r:0", "r:0:c", "r:0:b300"]]
    l0, l1, l2 = lines

    config = AggregationConfig(action_evs=False, global_freq=False)
    ag = aggregate_single_file(t, lines, conf=config)
    ag = {l.line_str: df for l, df in ag.items()}
    ag0 = ag[l0.line_str].iloc[0]  # Get first row as Series
    ag1 = ag[l1.line_str].iloc[0]  # Get first row as Series
    ag2 = ag[l2.line_str].iloc[0]

    assert ag0["Flop"] == "Kh7h2c"
    assert ag0["OOP EV"] == pytest.approx(165.60, rel=1e-2)
    assert ag0["IP EV"] == pytest.approx(132.90, rel=1e-2)
    assert ag0["OOP Equity"] == pytest.approx(0.52867, rel=1e-5)
    assert ag0["IP Equity"] == pytest.approx(0.47133, rel=1e-5)
    assert ag0["Check Freq"] == pytest.approx(59.09, rel=1e-2)
    assert ag0["Bet 300 Freq"] == pytest.approx(40.91, rel=1e-2)
    assert ag0["Bet 850 Freq"] == pytest.approx(0.0)

    with pytest.raises(KeyError):
        _ = ag0["Global Freq"]
    with pytest.raises(KeyError):
        _ = ag0["Check EV"]
    with pytest.raises(KeyError):
        _ = ag0["Bet 300 EV"]
    with pytest.raises(KeyError):
        _ = ag0["Bet 850 EV"]

    assert ag1["Flop"] == "Kh7h2c"
    assert ag1["OOP EV"] == pytest.approx(141.65, rel=1e-2)
    assert ag1["IP EV"] == pytest.approx(156.85, rel=1e-2)
    assert ag1["OOP Equity"] == pytest.approx(0.5179, rel=1e-4)
    assert ag1["IP Equity"] == pytest.approx(0.4821, rel=1e-4)
    assert ag1["Check Freq"] == pytest.approx(90.04, rel=1e-2)
    assert ag1["Bet 300 Freq"] == pytest.approx(9.96, rel=1e-2)
    assert ag1["Bet 850 Freq"] == pytest.approx(0.00, rel=1e-2)

    with pytest.raises(KeyError):
        _ = ag1["Global Freq"]
    with pytest.raises(KeyError):
        _ = ag1["Check EV"]
    with pytest.raises(KeyError):
        _ = ag1["Bet 300 EV"]
    with pytest.raises(KeyError):
        _ = ag1["Bet 850 EV"]


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_single_file_custom_config_02(solver, test_tree):
    t = get_test_tree()
    s = make_solver()
    s.load_tree(t)
    lines = [Line(l) for l in ["r:0", "r:0:c", "r:0:b300"]]
    l0, l1, l2 = lines

    config = AggregationConfig(action_evs=False, global_freq=True)
    ag = aggregate_single_file(t, lines, conf=config)
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

    with pytest.raises(KeyError):
        _ = ag0["Check EV"]
    with pytest.raises(KeyError):
        _ = ag0["Bet 300 EV"]
    with pytest.raises(KeyError):
        _ = ag0["Bet 850 EV"]


    assert ag1["Flop"] == "Kh7h2c"
    assert ag1["Global Freq"] == pytest.approx(0.590929, rel=1e-5)
    assert ag1["OOP EV"] == pytest.approx(141.65, rel=1e-2)
    assert ag1["IP EV"] == pytest.approx(156.85, rel=1e-2)
    assert ag1["OOP Equity"] == pytest.approx(0.5179, rel=1e-4)
    assert ag1["IP Equity"] == pytest.approx(0.4821, rel=1e-4)
    assert ag1["Check Freq"] == pytest.approx(90.04, rel=1e-2)
    assert ag1["Bet 300 Freq"] == pytest.approx(9.96, rel=1e-2)
    assert ag1["Bet 850 Freq"] == pytest.approx(0.00, rel=1e-2)

    with pytest.raises(KeyError):
        _ = ag1["Check EV"]
    with pytest.raises(KeyError):
        _ = ag1["Bet 300 EV"]
    with pytest.raises(KeyError):
        _ = ag1["Bet 850 EV"]


@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_single_file_custom_config_03(solver, test_tree):
    t = get_test_tree()
    s = make_solver()
    s.load_tree(t)
    lines = [Line(l) for l in ["r:0", "r:0:c", "r:0:b300"]]
    l0, l1, l2 = lines

    config = AggregationConfig(action_evs=True, global_freq=False)
    ag = aggregate_single_file(t, lines, conf=config)
    ag = {l.line_str: df for l, df in ag.items()}
    ag0 = ag[l0.line_str].iloc[0]  # Get first row as Series
    ag1 = ag[l1.line_str].iloc[0]  # Get first row as Series
    ag2 = ag[l2.line_str].iloc[0]

    assert ag0["Flop"] == "Kh7h2c"
    assert ag0["OOP EV"] == pytest.approx(165.60, rel=1e-2)
    assert ag0["IP EV"] == pytest.approx(132.90, rel=1e-2)
    assert ag0["OOP Equity"] == pytest.approx(0.52867, rel=1e-5)
    assert ag0["IP Equity"] == pytest.approx(0.47133, rel=1e-5)
    assert ag0["Check Freq"] == pytest.approx(59.09, rel=1e-2)
    assert ag0["Bet 300 Freq"] == pytest.approx(40.91, rel=1e-2)
    assert ag0["Bet 850 Freq"] == pytest.approx(0.0)
    assert ag0["Check EV"] == pytest.approx(141.65, rel=1e-2)
    assert ag0["Bet 300 EV"] == pytest.approx(200.20, rel=1e-2)
    assert np.isnan(ag0["Bet 850 EV"])

    with pytest.raises(KeyError):
        _ = ag0["Global Freq"]

    assert ag1["Flop"] == "Kh7h2c"
    assert ag1["OOP EV"] == pytest.approx(141.65, rel=1e-2)
    assert ag1["IP EV"] == pytest.approx(156.85, rel=1e-2)
    assert ag1["OOP Equity"] == pytest.approx(0.5179, rel=1e-4)
    assert ag1["IP Equity"] == pytest.approx(0.4821, rel=1e-4)
    assert ag1["Check Freq"] == pytest.approx(90.04, rel=1e-2)
    assert ag1["Bet 300 Freq"] == pytest.approx(9.96, rel=1e-2)
    assert ag1["Bet 850 Freq"] == pytest.approx(0.00, rel=1e-2)
    assert ag1["Check EV"] == pytest.approx(148.99, rel=1e-2)
    assert ag1["Bet 300 EV"] == pytest.approx(227.95, rel=1e-2)
    assert np.isnan(ag1["Bet 850 EV"])

    with pytest.raises(KeyError):
        _ = ag1["Global Freq"]

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_get_sorted_actions():
    result = ag.get_sorted_actions("r:0:c:b18:c:4d:c:b73:c".split(":"))
    assert(result[0]=="r")

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_get_actions_to_strats(QJ4_c_b18_b54):
    solver = QJ4_c_b18_b54.solver
    node_id = QJ4_c_b18_b54.node.node_id
    results = ag.get_actions_to_strats(solver,
                                      node_id,
                                      solver.show_children_actions(node_id))

    # results = {'b280': [...], 'b111': [...], 'f': [...], 'c': [...]}
    for result in results.values():
        assert len(result) == 1326

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_get_real_action_freqs(QJ4_c_b18_b54):
    node_id = "r:0:c:b18:b54"
    actions = QJ4_c_b18_b54.solver.show_children_actions(node_id)
    sorted_actions = ag.get_sorted_actions(actions)
    result = ag.get_real_action_freqs(QJ4_c_b18_b54, node_id, "IP",sorted_actions)
    assert abs(result[0] - 34.11) < 0.1
    assert abs(result[1] - 59.58) < 0.1
    assert abs(result[2] - 2.8) < 0.1
    assert abs(result[3] - 3.49) < 0.1

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_compute_row_matchups(QJ4_c_b18_b54):
    ag_config = ag.AggregationConfig(global_freq=False,
                                     evs=False,
                                     equities=False,
                                     action_freqs=False,
                                     action_evs=False,
                                     matchups=True)

    result = ag.compute_row(ag_config, QJ4_c_b18_b54, 1)

    # board
    assert result[0] == "QsJs4h"

    # global_freq
    assert close_enough(result[1], 22676244.371, 0.1, False)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_compute_row(QJ4_c_b18_b54):
    ag_config = AggregationConfig(global_freq=True,
                                     evs=True,
                                     equities=True,
                                     action_freqs=True,
                                     action_evs=True,
                                     matchups=False)

    children_actions = QJ4_c_b18_b54.available_actions()
    sorted_actions = ag.get_sorted_actions(children_actions)
    result = ag.compute_row(ag_config, QJ4_c_b18_b54, 1,children_actions,sorted_actions)

    # board
    assert result[0] == "QsJs4h"

    # global_freq
    assert close_enough(result[1], 0.4255, 0.1)

    # evs
    assert close_enough(result[2], 97.39, 0.1)
    assert close_enough(result[3], 29.60, 0.1)

    # eqs
    assert close_enough(result[4], 0.5749, 0.1)
    assert close_enough(result[5], 0.425, 0.1)

    # children action_freqs
    assert close_enough(result[6], 34.11, 0.1)  # fold
    assert close_enough(result[7], 59.58, 0.1)  # call
    assert close_enough(result[8], 2.8038, 0.1)  # b119
    assert close_enough(result[9], 3.4964, 0.1)  # b280

    # children action_evs (sum ev for every combo in node)
    assert close_enough(result[10], 0, 0.1)  # fold
    assert close_enough(result[11], 44.33, 0.1)  # call
    assert close_enough(result[12], 55.17, 0.1)  # b119
    assert close_enough(result[13], 47.10, 0.1)  # b280

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_line_for_solver(QJ4_c_b18_b54):
    ag_config = ag.AggregationConfig(equities=False,
                                evs=False,
                                action_freqs=False,
                                action_evs=False,
                                global_freq=True,
                                matchups=True)

    result = ag.aggregate_line_for_solver(QJ4_c_b18_b54.board(),
                                          QJ4_c_b18_b54.solver,
                                          Line(QJ4_c_b18_b54.node.node_id),
                                          ag_config,)

    assert close_enough(result['Global Freq'][0],0.42,0.1)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_lines_for_solver(QJ4_c_b18_b54):
    ag_config = ag.AggregationConfig(equities=False,
                                evs=False,
                                action_freqs=False,
                                action_evs=False,
                                global_freq=True,
                                matchups=True)

    result = ag.aggregate_lines_for_solver(QJ4_c_b18_b54.solver,
                                           [Line(QJ4_c_b18_b54.node.node_id),
                                                            Line(QJ4_c_b18_b54.node.parent().node_id)],
                                           ag_config)

    assert close_enough(result[Line(QJ4_c_b18_b54.node.node_id)]['Global Freq'][0],0.42,0.1)
    assert close_enough(result[Line(QJ4_c_b18_b54.node.parent().node_id)]['Global Freq'][0], 1, 0.1)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_single_file(file_path_cfrQJ4c):
    ag_config = ag.AggregationConfig(equities=False,
                                evs=False,
                                action_freqs=False,
                                action_evs=False,
                                global_freq=True,
                                matchups=True)

    line_1 = Line("r:0:c:b18:b54",effective_stack=280)
    line_2 = Line("r:0:c:b18",effective_stack=280)
    result = ag.aggregate_single_file(file_path_cfrQJ4c,
                                      [line_1,
                                            line_2],
                                       ag_config)

    assert close_enough(result[line_1]['Global Freq'][0],0.42,0.1)
    assert close_enough(result[line_2]['Global Freq'][0], 1, 0.1)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_files_in_dir_action_freqs_only(file_path_cfrQJ4c):
    new_set_path = str(importlib.resources.files("pious.pio.resources.database.very_small"))

    line_1 = Line("r:0:c:b18:b54",effective_stack=280)
    line_2 = Line("r:0:c:b18",effective_stack=280)

    lines_to_aggregate = ag.LinesToAggregate(
        lines=[line_1,line_2],
        flop=False,
        turn=False,
        river=False,
    )

    result = ag.aggregate_files_in_dir(
        new_set_path,
        lines_to_aggregate,
        ag.AggregationConfig(equities=False,
                                evs=False,
                                action_freqs=True,
                                action_evs=False,
                                global_freq=False,
                                matchups=True),
        debug=False,
        print_progress=False
    )

    result[line_1]['Matchups'] =result[line_1]['Matchups'].apply(lambda x: f'{x:.1f}')

    print(line_1)
    print(result[line_1].head())
    print(line_2)
    print(result[line_2].head())
    # assert close_enough(result[line_1]['Global Freq'][0],0.42,0.1)
    # assert close_enough(result[line_2]['Global Freq'][0], 1, 0.1)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_spot_data_children_matchups(QJ4_c_b18_b54):
    total_matchups = QJ4_c_b18_b54.total_matchups(0)
    children = QJ4_c_b18_b54.solver.show_children(QJ4_c_b18_b54.node.node_id)
    children_matchups = []

    for child in children:
        eqs, matchups, total_eq = QJ4_c_b18_b54.solver.calc_eq_node(0, child.node_id)
        children_matchups.append(sum(matchups))

    assert close_enough(total_matchups,sum(children_matchups),0.1,False)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_spot_data(QJ4_c_b18_b54):
    QJ4_c_b18_b54.hand_evs(0)
    assert close_enough(QJ4_c_b18_b54.ev(0),97.39,0.1)
    assert close_enough(QJ4_c_b18_b54.total_matchups(0), 11452.65, 0.1)

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_cmd_vsmall_flop(database_very_small_path):
    line_1 = "r:0:c:b18:b54"
    line_2 = "r:0:c:b18"

    agg_exec.aggregate_cmd(
        cfr_file_or_sim_dir=database_very_small_path,
        lines=[line_1,line_2],
        flop=False,
        turn=False,
        river=False,
        out=None,
        print_results=True,
        overwrite=False,
        progress=False,
    )

@pytest.mark.skipif(os.name != "nt", reason="Only runs on Windows")
def test_aggregate_cmd_vsmall_turn(database_very_small_path):
    line_1 = "r:0:c:b18:c:?:c:b73"

    agg_exec.aggregate_cmd(
        cfr_file_or_sim_dir=database_very_small_path,
        lines=[line_1],
        flop=False,
        turn=False,
        river=False,
        out=None,
        print_results=True,
        overwrite=False,
        progress=False,
    )

@pytest.mark.skip(reason="Long running test")
def test_aggregate_cmd_vsmall_river(database_very_small_path):
    line_1 = "r:0:c:b18:c:?:c:c:?:b73"

    agg_exec.aggregate_cmd(
        cfr_file_or_sim_dir=database_very_small_path,
        lines=[line_1],
        flop=False,
        turn=False,
        river=False,
        out=None,
        print_results=True,
        overwrite=False,
        progress=False,
    )
