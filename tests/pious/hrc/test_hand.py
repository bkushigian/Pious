from pious.hrc.resources import get_test_hrc_sim
from pious.hrc.hand import HRCNode

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
    n0: HRCNode = sim.node_cache[0]
    assert n0.player == 0
    assert n0.street == 0
    assert n0.children == 2
    assert n0.sequence == []
    assert len(n0.actions) == 2
    assert (
        n0.actions[0].type == "F"
        and n0.actions[0].amount == 0
        and n0.actions[0].next_id == 1
    )
    assert (
        n0.actions[1].type == "R"
        and n0.actions[1].amount == 2500
        and n0.actions[1].next_id == 155
    )

    hands = n0.hands
    assert hands["22"].weight == 1.0
    assert hands["22"].played[0] == 0.8324
    assert hands["22"].played[1] == 0.1676
