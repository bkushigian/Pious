from pious.hrc.resources import get_test_hrc_sim

sim = get_test_hrc_sim()
nodes = sim.nodes

def test_sim_settings():
    hand_data = sim.settings.hand_data
    assert hand_data.stacks == [100000, 100000, 100000, 100000, 100000, 100000]
    assert hand_data.blinds == [1000, 500, 0]
    assert not hand_data.skip_sb
    assert not hand_data.moving_bu
    assert hand_data.ante_type == "REGULAR"

    engine = sim.settings.engine
    assert engine.type == "montecarlo"
    assert engine.max_active == 4
    assert engine.configuration.preflop_abstractions == 169
    assert engine.configuration.flop_abstractions == 16384
    assert engine.configuration.turn_abstractions == 16384
    assert engine.configuration.river_abstractions == 16384


    eq_model = sim.settings.eq_model
    assert eq_model.rake_cap == 80
    assert eq_model.rake_pct == 0.05
    assert eq_model.id == "chipev"
    assert eq_model.nfnd
    assert eq_model.raked

def test_sim_nodes():
    n0 = sim.node_cache[0]
    assert n0.player == 0
    assert n0.street == 0
    assert n0.children == 2
    assert n0.sequence == []
    assert len(n0.actions) == 2