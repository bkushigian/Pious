from typing import List, Optional
import pious.hrc.hand as hrc_hand

from pious.hrc.hand import PreviousAction, Action


class GameState:
    def __init__(
        self,
        pot,
        stacks,
        player_names,
        bets,
        in_hand,
        current_player,
        available_actions=None,
    ):
        self.pot: int = pot
        self.stacks: List[int] = list(stacks)
        self.num_players: int = len(stacks)
        self.player_names: List[str] = player_names
        self.bets: List[int] = list(bets)
        self.in_hand: List[bool] = list(in_hand)
        self.current_player: int = current_player
        self.available_actions: Optional[List[Action]] = available_actions

    def apply_previous_action(self, action: PreviousAction) -> "GameState":
        a = action
        if a.player != self.current_player:
            raise RuntimeError(
                f"Illegal state: current player {self.current_player} is not the player applying action {a.player}"
            )

        if not self.in_hand[self.current_player]:
            raise RuntimeError(
                f"Illegal State: tried to take action {a.type}:{a.amount} for player {a.player} not in pot"
            )

        # Copy current data to modify and pass to new GameState
        pot = self.pot
        stacks = list(self.stacks)
        bets = list(self.bets)
        in_hand = list(self.in_hand)
        current_player = self.current_player
        next_player = (current_player + 1) % self.num_players

        if a.type == "F":
            in_hand[current_player] = False

        # Raises record the _total amount_ being raised to
        elif a.type == "R":
            new_money_entering_pot = a.amount - bets[current_player]
            stacks[current_player] -= new_money_entering_pot
            pot += new_money_entering_pot
            bets[current_player] = a.amount

        # Calls record the amount _of additional money_ the player puts in to
        # match the bet
        elif a.type == "C":
            stacks[current_player] -= a.amount
            pot += a.amount
            bets[current_player] += a.amount

        return GameState(pot, stacks, self.player_names, bets, in_hand, next_player)

    def __str__(self):
        return f"GameState(pot={self.pot}, stacks={self.stacks}, num_players={self.num_players}, bets={self.bets}, in_hand={self.in_hand}, current_player={self.current_player}, available_actions={self.available_actions})"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return (
            isinstance(other, GameState)
            and self.pot == other.pot
            and self.stacks == other.stacks
            and self.num_players == other.num_players
            and self.bets == other.bets
            and self.in_hand == other.in_hand
            and self.current_player == other.current_player
            and self.available_actions == other.available_actions
        )

    def as_json(self):
        return {
            "pot": self.pot,
            "stacks": self.stacks,
            "player_names": self.player_names,
            "bets": self.bets,
            "in_hand": self.in_hand,
            "current_player": self.current_player,
            "available_actions": [a.as_json() for a in self.available_actions],
        }


class Game:
    def __init__(
        self,
        sim: hrc_hand.HRCSim,
        node_id=0,
        player_names=None,
    ):
        self.sim = sim
        self.node: hrc_hand.HRCNode = sim.get_node(node_id)

        # Compute initial game state (after antes and blinds have gone in)
        pot = 0

        stacks = [s for s in sim.settings.hand_data.stacks]
        num_players = len(stacks)

        if player_names is None:
            names = ["lj", "hj", "co", "bn", "sb", "bb"]
        else:
            names = player_names
        names = names[-num_players:]

        bets = [0 for _ in stacks]
        in_hand = [True for _ in stacks]
        blinds = sim.settings.hand_data.blinds
        bb, sb, ante = blinds

        # Apply antes: these go
        for i in range(len(stacks)):
            stacks[i] -= ante
        pot += len(stacks) * ante

        # Apply blinds
        stacks[-2] -= sb
        bets[-2] += sb
        pot += sb

        stacks[-1] -= bb
        bets[-1] += bb
        pot += bb

        # Game state after posting blinds/antes
        self.game_state_at_hand_start = GameState(pot, stacks, names, bets, in_hand, 0)
        self.game_states = [self.game_state_at_hand_start]
        for action in self.node.sequence:
            prior_game_state = self.game_states[-1]
            next_game_state = prior_game_state.apply_previous_action(action)
            self.game_states.append(next_game_state)

        self.game_state_at_node = self.game_states[-1]
        self.game_state_at_node.available_actions = self.node.actions
