from typing import Optional, Callable
from .hands import Hand


class HandCategory:
    def __init__(
        self, name: str, parent: Optional["HandCategory"], indicator: Callable
    ):
        self.name = name
        self._parent = parent
        self._indicator = indicator
        self._children = {}

    def __call__(self, hand: Hand):
        return self._indicator(hand)

    def register_subcategory(self, sub: "HandCategory"):
        if sub.name in self._children:
            raise ValueError(
                f"HandCategory {self} already has subcategory with name {sub.name}"
            )
        self._children[sub.name] = sub


class HandCategorizer:

    POCKET_PAIR = 0
    BOARD_PAIR = 1
    REGULAR_PAIR = 2

    def __init__(self):
        self.categories = [
            "High Card",
            "Pair",
            "Two Pair",
            "Trips",
            "Straight",
            "Flush",
            "Full House",
            "Quads",
            "Straight Flush",
        ]

    def categorize(self, hand: Hand):
        hand.evaluate()
        ht = hand._hand_type
        match ht:
            case Hand.HIGH_CARD:
                return self.categories[ht]
            case Hand.PAIR:
                pair_type, board_cards_seen, kicker = self.get_pair_category(hand)
                return pretty_pair(pair_type, board_cards_seen, kicker)
        return self.categories[hand._hand_type]

    def get_pair_category(self, hand: Hand):
        assert hand._hand_type == Hand.PAIR
        board_cards_seen = 0
        kicker_count = 0
        kicker = None
        pair_type = None
        pair_strength = None
        # Iterate over hand rankg counts, board rank counts, and rank counts
        for hrc, brc, rc in zip(
            hand._hand_rank_count[::-1],
            hand._board_rank_count[::-1],
            hand._rank_count[::-1],
        ):
            if brc > 0:
                board_cards_seen += 1
            elif kicker is None:
                kicker_count += 1
                if hrc > 0:
                    kicker = kicker_count

            if rc == 2:
                # If this is the pair, determine the type of pair
                if brc == 2:
                    pair_type, pair_strength = (
                        HandCategorizer.BOARD_PAIR,
                        board_cards_seen,
                    )
                elif hrc == 2:
                    pair_type, pair_strength = (
                        HandCategorizer.POCKET_PAIR,
                        board_cards_seen,
                    )
                else:
                    pair_type, pair_strength = (
                        HandCategorizer.REGULAR_PAIR,
                        board_cards_seen,
                    )
        return pair_type, pair_strength, kicker


def pretty_pair(pair_type, board_cards_seen, kicker):
    match pair_type:
        case HandCategorizer.POCKET_PAIR:
            if board_cards_seen == 0:
                return "OverPair"
            else:
                return f"UnderPair[{board_cards_seen}]"
        case HandCategorizer.REGULAR_PAIR:
            match board_cards_seen:
                case 1:
                    return f"TopPair[{kicker}]"
                case 2:
                    return f"2ndPair[{kicker}]"
                case 3:
                    return f"3rdPair[{kicker}]"
                case 4:
                    return f"4thPair[{kicker}]"
                case 5:
                    return f"5thPair[{kicker}]"
            return "Unknown"
        case HandCategorizer.BOARD_PAIR:
            return f"BoardPair[{kicker}]"
