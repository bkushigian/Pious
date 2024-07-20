from pious.hrc.resources import get_test_hrc_sim
from pious.hrc.hand import HRCNode, HRCSim
from pious.hrc.game_state import Game, GameState

sim: HRCSim = get_test_hrc_sim()


def test_game_state_root():
    # Blinds have been posted, utg to act
    # Node id: 0
    game = Game(sim, 0)
    s: GameState = game.game_state_at_hand_start
    e: GameState = GameState(
        1500,
        [100000, 100000, 100000, 100000, 100000 - 500, 100000 - 1000],
        ["lj", "hj", "co", "bn", "sb", "bb"],
        [0, 0, 0, 0, 500, 1000],
        [True, True, True, True, True, True],
        0,
        game.node.actions,
    )
    assert s == e

    actual_json = s.as_json()
    expected_json = {
        "pot": 1500,
        "stacks": [100000, 100000, 100000, 100000, 100000 - 500, 100000 - 1000],
        "player_names": ["lj", "hj", "co", "bn", "sb", "bb"],
        "bets": [0, 0, 0, 0, 500, 1000],
        "in_hand": [True, True, True, True, True, True],
        "community_cards": [],
        "current_player": 0,
        "available_actions": [
            {"player": None, "type": "F", "amount": 0, "next_id": 1},
            {"player": None, "type": "R", "amount": 2500, "next_id": 155},
        ],
    }

    assert actual_json == expected_json


def test_game_state_r_f():
    # Test after lj folds
    # Node id: 1
    game = Game(sim, 1)
    s: GameState = game.game_state_at_node
    e: GameState = GameState(
        1500,
        [100000, 100000, 100000, 100000, 100000 - 500, 100000 - 1000],
        ["lj", "hj", "co", "bn", "sb", "bb"],
        [0, 0, 0, 0, 500, 1000],
        [False, True, True, True, True, True],
        1,
        game.node.actions,
    )
    assert s == e, f"Actual state\n    {s}\nnot equal to expected state\n    {e}"

    actual_json = s.as_json()
    expected_json = {
        "pot": 1500,
        "stacks": [100000, 100000, 100000, 100000, 100000 - 500, 100000 - 1000],
        "player_names": ["lj", "hj", "co", "bn", "sb", "bb"],
        "bets": [0, 0, 0, 0, 500, 1000],
        "in_hand": [False, True, True, True, True, True],
        "community_cards": [],
        "current_player": 1,
        "available_actions": [
            {"player": None, "type": "F", "amount": 0, "next_id": 2},
            {"player": None, "type": "R", "amount": 2500, "next_id": 65},
        ],
    }

    assert actual_json == expected_json


def test_game_state_r_r2500():
    # Test after lj raises to 2.5bb
    # Node id: 155
    game = Game(sim, 155)
    s: GameState = game.game_state_at_node
    e: GameState = GameState(
        4000,
        [100000 - 2500, 100000, 100000, 100000, 100000 - 500, 100000 - 1000],
        ["lj", "hj", "co", "bn", "sb", "bb"],
        [2500, 0, 0, 0, 500, 1000],
        [True, True, True, True, True, True],
        1,
        game.node.actions,
    )
    assert s == e, f"Actual state\n    {s}\nnot equal to expected state\n    {e}"

    actual_json = s.as_json()
    expected_json = {
        "pot": 4000,
        "stacks": [100000 - 2500, 100000, 100000, 100000, 100000 - 500, 100000 - 1000],
        "player_names": ["lj", "hj", "co", "bn", "sb", "bb"],
        "bets": [2500, 0, 0, 0, 500, 1000],
        "in_hand": [True, True, True, True, True, True],
        "community_cards": [],
        "current_player": 1,
        "available_actions": [
            {"player": None, "type": "F", "amount": 0, "next_id": 156},
            {"player": None, "type": "R", "amount": 7500, "next_id": 246},
        ],
    }

    assert actual_json == expected_json


def test_game_state_r_r2500_r7500():
    # Test after lj raises to 2.5bb, hj raises to 7.5bb
    # Node id: 246
    game = Game(sim, 246)
    s: GameState = game.game_state_at_node
    e: GameState = GameState(
        1500 + 2500 + 7500,
        [100000 - 2500, 100000 - 7500, 100000, 100000, 100000 - 500, 100000 - 1000],
        ["lj", "hj", "co", "bn", "sb", "bb"],
        [2500, 7500, 0, 0, 500, 1000],
        [True, True, True, True, True, True],
        2,
        game.node.actions,
    )
    assert s == e, f"Actual state\n    {s}\nnot equal to expected state\n    {e}"

    actual_json = s.as_json()
    expected_json = {
        "pot": 1500 + 2500 + 7500,
        "stacks": [
            100000 - 2500,
            100000 - 7500,
            100000,
            100000,
            100000 - 500,
            100000 - 1000,
        ],
        "player_names": ["lj", "hj", "co", "bn", "sb", "bb"],
        "bets": [2500, 7500, 0, 0, 500, 1000],
        "in_hand": [True, True, True, True, True, True],
        "community_cards": [],
        "current_player": 2,
        "available_actions": [
            {"player": None, "type": "F", "amount": 0, "next_id": 247},
            {"player": None, "type": "R", "amount": 19000, "next_id": 295},
        ],
    }

    assert actual_json == expected_json


def test_game_state_r_r2500_f_f_f_f_r12000():
    # Test after lj raises to 2.5bb, hj raises to 7.5bb
    # Node id: 246
    game = Game(sim, 160)
    s: GameState = game.game_state_at_node
    e: GameState = GameState(
        500 + 2500 + 12000,
        [100000 - 2500, 100000, 100000, 100000, 100000 - 500, 100000 - 12000],
        ["lj", "hj", "co", "bn", "sb", "bb"],
        [2500, 0, 0, 0, 500, 12000],
        [True, False, False, False, False, True],
        0,
        game.node.actions,
    )
    assert s.pot == e.pot
    assert s.stacks == e.stacks
    assert s.num_players == e.num_players
    assert s.player_names == e.player_names
    assert s.bets == e.bets
    assert s.in_hand == e.in_hand
    assert s.current_player == e.current_player
    assert s.available_actions == e.available_actions
    assert s == e, f"Actual state\n    {s}\nnot equal to expected state\n    {e}"

    actual_json = s.as_json()
    expected_json = {
        "pot": 500 + 2500 + 12000,
        "stacks": [
            100000 - 2500,
            100000,
            100000,
            100000,
            100000 - 500,
            100000 - 12000,
        ],
        "player_names": ["lj", "hj", "co", "bn", "sb", "bb"],
        "bets": [2500, 0, 0, 0, 500, 12000],
        "in_hand": [True, False, False, False, False, True],
        "community_cards": [],
        "current_player": 0,
        "available_actions": [
            {"player": None, "type": "F", "amount": 0, "next_id": None},
            {"player": None, "type": "C", "amount": 9500, "next_id": None},
            {"player": None, "type": "R", "amount": 23000, "next_id": 161},
        ],
    }

    assert actual_json == expected_json
