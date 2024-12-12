from typing import Optional, Callable, Tuple

from pious.hands import Hand, count_ones
from .hands import Hand, count_ones, u32
import itertools


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
        hand.compute_draws()
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


class StraightDrawMasks:
    """
    This generates all masks for straight draws.

    Strength of straight draw masks
    1. OESD/Double Gutter (8-out)
    2. Gutter/A-wheel/A-broadway (4out)
    3. Backdoor Straight Draw

    Some of the returned masks need to be shifted to be accurate (namely, any of
    the non-a-high masks). The shifted masks will cover n-bit windows and need
    to be shifted. For instance, an OESD is just 0xf and covers a 5 bit window.
    So 2345 would correspond to 0xf, 3456 would correspond to 0xf << 1, all the
    way up to 0xf << 8, which corresponds to 9TJQK (note that the 5th bit is
    unset: this works out because JQKA is not an OESD).

    """

    def __init__(self):

        # OESDs are 4 contiguous ranks in a row
        self.oesd_5_card_masks = {u32(0xF)}

        # Differing bit windows. That's okay, we can still do the normal shifting
        # assuming 7 bit widths (there will be 1 always-false check against the 2nd
        # value)
        self.double_gutter_7_card_masks = {
            u32(0b11011101),
            u32(0b01011101),
            u32(0b11011011),
        }
        self.gutshot_5_card_masks = {u32(0b10111), u32(0b11011), u32(0b11101)}

        self.a_high_broadway_13_card_masks = {
            u32(0b1111000000000),
            u32(0b1110100000000),
            u32(0b1101100000000),
            u32(0b1011100000000),
        }
        self.a_high_wheel_13_card_masks = {
            u32(0b1000000001110),
            u32(0b1000000001101),
            u32(0b1000000001011),
            u32(0b1000000000111),
        }
        self.backdoor_5_card_masks = set()
        self.backdoor_4_5_high_masks = {
            u32(0b00111),
            u32(0b01011),
            u32(0b01101),
            u32(0b01110),
        }
        self.backdoor_wheel_masks = {
            u32(0b1000000000011),
            u32(0b1000000000101),
            u32(0b1000000000110),
            u32(0b1000000001001),
            u32(0b1000000001001),
            u32(0b1000000001010),
            u32(0b1000000001100),
        }

        for r1, r2 in itertools.combinations(range(4), 2):
            mask = u32(1 << 4)
            mask += u32(1 << r1)
            mask += u32(1 << r2)
            self.backdoor_5_card_masks.add(mask)

    def categorize(self, hand: Hand) -> Tuple[str, int]:

        rankset = hand.get_rankset()
        board_rankset = hand.get_board_rankset()
        hand_rankset = hand.get_hand_rankset()

        gutshot = None
        a_high_broadway = None
        a_high_wheel = None
        if rankset & 1 << 12:
            # Compute A-high broadway/wheels
            if rankset & 0b1111100000000 in self.a_high_broadway_13_card_masks:
                a_high_broadway = (
                    "A_HIGH_BROADWAY",
                    count_ones((0b1111100000000 & hand_rankset) & ~board_rankset),
                )

            elif rankset & 0b1000000001111 in self.a_high_wheel_13_card_masks:
                a_high_wheel = (
                    "A_HIGH_WHEEL",
                    count_ones((0b1000000001111 & hand_rankset) & ~board_rankset),
                )

        # Check for 8-out straight draws
        for offset in range(13 - 5, -1, -1):
            ranks = rankset >> offset
            board_ranks = board_rankset >> offset
            hand_ranks = hand_rankset >> offset

            hand_5_rank_window = hand_ranks & 0x1F
            hand_7_rank_window = hand_ranks & 0xFF
            num_hand_ranks_5_card_window = count_ones(hand_5_rank_window & ~board_ranks)
            num_hand_ranks_7_card_window = count_ones(hand_7_rank_window & ~board_ranks)

            # Double Gutter
            if num_hand_ranks_7_card_window > 0:

                if ranks & 0x7F in self.double_gutter_7_card_masks:
                    return "DOUBLE_GUTTER", num_hand_ranks_7_card_window
                if ranks & 0xFF in self.double_gutter_7_card_masks:
                    return "DOUBLE_GUTTER", num_hand_ranks_7_card_window
            # OESD
            if num_hand_ranks_5_card_window > 0:
                if ranks & 0x1F in self.oesd_5_card_masks:
                    return "OESD", num_hand_ranks_5_card_window

            if gutshot is None:
                if ranks & 0x1F in self.gutshot_5_card_masks:
                    gutshot = "GUTSHOT", num_hand_ranks_5_card_window

        # Check for 4-out straight draws
        if a_high_broadway:
            return a_high_broadway
        if a_high_wheel:
            return a_high_wheel
        if gutshot:
            return gutshot

        # Now backdoors
        for offset in range(13 - 5, -1, -1):
            ranks = rankset >> offset
            if ranks & 0x1F in self.backdoor_5_card_masks:

                # We need to compute the number of cards in hand that contribute.
                hand_ranks = hand_rankset >> offset
                board_ranks = board_rankset >> offset
                hand_5_rank_window = hand_ranks & 0x1F
                num_hand_ranks_5_card_window = count_ones(
                    hand_5_rank_window & ~board_ranks
                )
                if num_hand_ranks_5_card_window > 0:
                    return "BACKDOOR_STRAIGHT_DRAW", num_hand_ranks_5_card_window

        if rankset & 0x100F in self.backdoor_wheel_masks:
            num_hand_ranks = count_ones((hand_rankset & 0x100F) & ~board_rankset)
            return "BACKDOOR_WHEEL_DRAW", num_hand_ranks

        # 5 high and 4 high
        masked = rankset & 0xF
        if masked in self.backdoor_4_5_high_masks:
            num_hand_ranks = count_ones((hand_rankset & 0xF) & ~board_rankset)
            return "BACKDOOR_STRAIGHT_DRAW", num_hand_ranks

        return "NO_STRAIGHT_DRAW", 0


class FlushDraws:
    def __init__(self):
        pass

    def categorize(self, hand: Hand) -> Tuple[str, int, int]:
        """
        Test for flush draws and return details about the draw, including:
        (DRAW_TYPE, N_CARDS, HIGHEST_CARD_IN_HAND)
        """
        max_suit_count = 0
        max_suit = -1
        second_max_suit = -1
        num_cards = 0
        suit_counts = hand.get_suit_count()

        # Get ranksets for each suit for both the entire hand+board and the board itself
        suit_ranksets = hand.get_suit_ranksets()
        hand_suit_ranksets = hand.get_hand_suit_ranksets()

        highest_draw_contributing_card_in_hand = -1
        for suit, count in enumerate(suit_counts):
            if count >= 3 and count > max_suit_count:
                hrs = hand_suit_ranksets[suit]
                n_cards = count_ones(hrs)

                if n_cards == 0:
                    # Skip: we do not contribute to the draw
                    continue
                num_cards = n_cards
                max_suit_count = count
                max_suit = suit

                if max_suit_count == 5:
                    break
                if max_suit_count == 4:
                    break
                if num_cards == 2:
                    break

            elif count == max_suit_count == 3:
                hrs = hand_suit_ranksets[suit]
                n_cards = count_ones(hrs)
                if n_cards == 0:
                    continue
                num_cards = n_cards
                second_max_suit = suit

        if max_suit_count < 3:
            return "NO_FLUSH_DRAW", 0, -1

        if max_suit_count >= 3:
            rs = suit_ranksets[max_suit]
            hrs = hand_suit_ranksets[max_suit]
            flag = 1 << 13
            card_strength_index = 0
            while flag > 0:
                flag = flag >> 1
                if rs & flag != 0:
                    if hrs & flag != 0:
                        highest_draw_contributing_card_in_hand = card_strength_index + 1
                        break
                else:
                    card_strength_index += 1
        if second_max_suit > -1:
            pass

        fd_type = ("", "", "", "BACKDOOR_FLUSH_DRAW", "FLUSH_DRAW", "FLUSH")[
            max_suit_count
        ]
        return fd_type, num_cards, highest_draw_contributing_card_in_hand
