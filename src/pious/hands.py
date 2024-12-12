"""
This module is responsible for various operations on NLHE hands, such as
categorization and ranking.
"""

import itertools
from typing import Tuple
import numpy as np
from ._hand_table import HAND_TABLE
from collections import namedtuple
from bisect import bisect

i32 = np.int32
u32 = np.uint32

_Hand = namedtuple("Hand", ["hand", "board"])

Card = np.uint8

_SUIT_STR = "cdhs"
_SUITS = {r: np.uint8(i) for (i, r) in enumerate(_SUIT_STR)}

_RANK_STR = "23456789TJQKA"
_RANKS = {r: np.uint8(i) for (i, r) in enumerate(_RANK_STR)}


def card_from_str(c: str) -> Card:
    r, s = c  # Must be length 2
    return Card(4 * _RANKS[r] + _SUITS[s])


def card_to_str(c: Card) -> str:
    r = c // 4
    s = c % 4
    return f"{_RANK_STR[r]}{_SUIT_STR[s]}"


def count_ones_in_nibble(nibble: int) -> int:
    x = nibble & 0xF
    match x:
        case 0b0000:
            return 0
        case 0b0001:
            return 1
        case 0b0010:
            return 1
        case 0b0011:
            return 2
        case 0b0100:
            return 1
        case 0b0101:
            return 2
        case 0b0110:
            return 2
        case 0b0111:
            return 3
        case 0b1000:
            return 1
        case 0b1001:
            return 2
        case 0b1010:
            return 2
        case 0b1011:
            return 3
        case 0b1100:
            return 2
        case 0b1101:
            return 3
        case 0b1110:
            return 3
        case 0b1111:
            return 4
    return 0


def count_ones(x) -> u32:
    """
    >>> expected = []
    >>> actual = []
    >>> import random
    >>> count_ones(31)
    np.uint32(5)
    >>> count_ones(3131)
    np.uint32(7)
    """
    _x = u32(x)
    n_ones = u32(0)
    while _x != 0:
        n_ones += u32(count_ones_in_nibble(_x))
        _x = _x >> 4
    return n_ones


def _count_ones_inefficient(x):
    """
    For testing, this is ground truth of count_ones()
    """
    return len(str(bin(x)[2:]).replace("0", ""))


def leading_zeros(x: u32) -> u32:
    n = u32(0)
    if u32(0xFFFF0000) & x == 0:
        n += 16
    else:
        x = x >> 16
    if 0x0000FF00 & x == 0:
        n += 8
    else:
        x = x >> 8
    if 0x000000F0 & x == 0:
        n += 4
    else:
        x = x >> 4
    if 0x0000000C & x == 0:
        n += 2
    else:
        x = x >> 2
    if 0x00000002 & x == 0:
        n += 1
    else:
        x = x >> 1
    if 0x00000001 & x == 0:
        n += 1
    return n


def leading_ones(x: u32) -> u32:
    n = u32(0)
    if u32(0xFFFF0000) & x != 0:
        n += 16
    else:
        x = x >> 16
    if 0x0000FF00 & x != 0:
        n += 8
    else:
        x = x >> 8
    if 0x000000F0 & x != 0:
        n += 4
    else:
        x = x >> 4
    if 0x0000000C & x != 0:
        n += 2
    else:
        x = x >> 2
    if 0x00000002 & x != 0:
        n += 1
    else:
        x = x >> 1
    if 0x00000001 & x != 0:
        n += 1
    return n


def keep_n_msb(x: u32, n: u32) -> u32:
    ret = 0
    for _ in range(n):
        bit = 1 << (leading_zeros(x) ^ 0x1F)
        x ^= bit
        ret |= bit
    return ret


_WHEEL = 0b1_0000_0000_1111


def find_straight(rankset: u32) -> u32:
    """
    Return the bit of the highest straight card, or 0 if none exists
    """
    is_straight = (
        rankset & (rankset << 1) & (rankset << 2) & (rankset << 3) & (rankset << 4)
    )
    if is_straight != 0:
        return keep_n_msb(is_straight, 1)
    elif (rankset & _WHEEL) == _WHEEL:
        return 1 << 3
    return u32(0)


def hand(hand, board, evaluate=False):
    """
    Get a Hand and optionally evaluate it.
    """
    h = Hand(hand, board)
    if evaluate:
        h._evaluate_internal()
    return h


class Hand(_Hand):
    """
    This class represents a hand on a board, and includes logic for describing
    if it is stronger or weaker than another hand.

    Attributes:
        hand: the string representation of the hole cards
        board: the string representation of the board
        hand_cards: the `Card` (u8) representation of the hole cards
        board_cards: the `Card` (u8) representation of the board cards
        all_cards: the u8 representation of all of the cards (hand plus board)

        _evaluation: the cached evaluation, computed by `Hand._evaluate_internal()`
        _hand_type: the cached flags representing the hand class
        _hand_distinguisher: the cached bitfield distinguishing between
            different hands of the same hand_type
    """

    STRAIGHT_FLUSH = 8
    QUADS = 7
    FULL_HOUSE = 6
    FLUSH = 5
    STRAIGHT = 4
    TRIPS = 3
    TWO_PAIR = 2
    PAIR = 1
    HIGH_CARD = 0

    def __init__(self, hand, board):
        self.hand_cards = [
            card_from_str(c) for c in [hand[i : i + 2] for i in range(0, len(hand), 2)]
        ]
        self.board_cards = [
            card_from_str(c)
            for c in [board[i : i + 2] for i in range(0, len(board), 2)]
        ]
        self.all_cards = self.hand_cards + self.board_cards
        self._evaluation = u32(0)
        self._hand_type = u32(0)
        self._hand_distinguisher = u32(0)
        # All Cards
        self._rankset = None
        self._rank_count = None
        self._rankset_suit = None
        self._rankset_of_count = None
        self._suit_count = None

        # Hand
        self._hand_rankset = None
        self._hand_rank_count = None
        self._hand_rankset_suit = None
        self._hand_rankset_of_count = None
        # Board
        self._board_rankset = None
        self._board_rank_count = None
        self._board_rankset_suit = None
        self._board_rankset_of_count = None
        self._board_extensive_details = None

    def is_straight_flush(self):
        self._evaluate_internal()
        return self._hand_type == Hand.STRAIGHT_FLUSH

    def is_quads(self):
        self._evaluate_internal()
        return self._hand_type == Hand.QUADS

    def is_full_house(self):
        self._evaluate_internal()
        return self._hand_type == Hand.FULL_HOUSE

    def is_flush(self):
        self._evaluate_internal()
        return self._hand_type == Hand.FLUSH

    def is_straight(self):
        self._evaluate_internal()
        return self._hand_type == Hand.STRAIGHT

    def is_trips(self):
        self._evaluate_internal()
        return self._hand_type == Hand.TRIPS

    def is_two_pair(self):
        self._evaluate_internal()
        return self._hand_type == Hand.TWO_PAIR

    def is_pair(self):
        self._evaluate_internal()
        return self._hand_type == Hand.PAIR

    def is_high_card(self):
        self._evaluate_internal()
        return self._hand_type == Hand.HIGH_CARD

    def evaluate(self) -> u32:
        evaluation = self._evaluate_internal()
        return bisect(HAND_TABLE, evaluation)

    def compute_draws(self):
        self._compute_flush_draws()
        self._compute_straight_draws()

    def _compute_flush_draws(self) -> Tuple[int, int]:
        """
        Compute if hand is a flush, flush draw, BDFD, or 2xBDFD,
        and the number of cards in hand that contribute to this
        """
        n_cards = 0
        BDFD = 2
        BDFD_TWICE = 3

        flush_type = 0
        for suit in range(4):
            sc = self._suit_count[suit]
            hsc = self._hand_suit_count[suit]
            if sc >= 3 and sc >= flush_type:
                if sc == 3:
                    # Assign to avoid a branch
                    ft = BDFD
                    if flush_type == BDFD and hsc == 1:
                        ft = BDFD_TWICE
                    flush_type = ft
                    n_cards += hsc
                else:
                    flush_type = sc
                    n_cards += hsc

        return flush_type, n_cards

    def _compute_straight_draws(self):
        pass

    def _evaluate_internal(self):
        if self._evaluation != 0:
            # Cache the result
            return self._evaluation
        # All Cards
        rankset = u32(0)
        rankset_suit = [u32(0), u32(0), u32(0), u32(0)]
        rankset_of_count = [u32(0), u32(0), u32(0), u32(0), u32(0)]
        rank_count = [u32(0) for _ in range(13)]
        suit_count = [u32(0), u32(0), u32(0), u32(0)]

        # Hand
        hand_rankset = u32(0)
        hand_rankset_suit = [u32(0), u32(0), u32(0), u32(0)]
        hand_rankset_of_count = [u32(0), u32(0), u32(0), u32(0), u32(0)]
        hand_rank_count = [u32(0) for _ in range(13)]
        hand_suit_count = [u32(0), u32(0), u32(0), u32(0)]

        # Board
        board_rankset = u32(0)
        board_rankset_suit = [u32(0), u32(0), u32(0), u32(0)]
        board_rankset_of_count = [u32(0), u32(0), u32(0), u32(0), u32(0)]
        board_rank_count = [u32(0) for _ in range(13)]

        for c in self.board_cards:
            r = u32(c // 4)
            s = u32(c % 4)
            rankset |= 1 << r
            rankset_suit[s] |= 1 << r
            rank_count[r] += 1

            board_rankset |= 1 << r
            board_rankset_suit[s] |= 1 << r
            board_rank_count[r] += 1

        for c in self.hand_cards:
            r = u32(c // 4)
            s = u32(c % 4)
            rankset |= 1 << r
            rankset_suit[s] |= 1 << r
            rank_count[r] += 1

            hand_rankset |= 1 << r
            hand_rankset_suit[s] |= 1 << r
            hand_rank_count[r] += 1

        for r in range(13):
            rankset_of_count[rank_count[r]] |= 1 << r
            board_rankset_of_count[board_rank_count[r]] |= 1 << r
            hand_rankset_of_count[hand_rank_count[r]] |= 1 << r

        flush_suit = u32(0xFFFFFFFF)
        for suit in range(4):
            c = count_ones(rankset_suit[suit])
            suit_count[suit] = c
            hand_suit_count[suit] = count_ones(hand_rankset_suit[suit])
            if c >= 5:
                flush_suit = suit

        is_straight = find_straight(rankset)
        flush = 0
        if flush_suit < 4:
            is_straight_flush = find_straight(rankset_suit[flush_suit])
            if is_straight_flush != 0:
                self._evaluation = (Hand.STRAIGHT_FLUSH << 26) | is_straight_flush
                return self._evaluation
            flush = (Hand.FLUSH << 26) | keep_n_msb(rankset_suit[flush_suit], 5)
        if rankset_of_count[4] != 0:
            remaining = keep_n_msb(rankset ^ rankset_of_count[4], 1)
            self._evaluation = (
                (Hand.QUADS << 26) | rankset_of_count[4] << 14 | remaining
            )
        elif count_ones(rankset_of_count[3]) == 2:
            trips = keep_n_msb(rankset_of_count[3], 1)
            pair = rankset_of_count[3] ^ trips
            self._evaluation = (Hand.FULL_HOUSE << 26) | (trips << 13) | pair
        elif rankset_of_count[3] != 0 and rankset_of_count[2] != 0:
            pair = keep_n_msb(rankset_of_count[2], 1)
            self._evaluation = (
                (Hand.FULL_HOUSE << 26) | (rankset_of_count[3] << 13) | pair
            )
        elif flush:
            self._evaluation = flush
        elif is_straight != 0:
            self._evaluation = (Hand.STRAIGHT << 26) | is_straight
        elif rankset_of_count[3] != 0:
            remaining = keep_n_msb(rankset_of_count[1], 2)
            self._evaluation = (
                (Hand.TRIPS << 26) | (rankset_of_count[3] << 13) | remaining
            )
        elif count_ones(rankset_of_count[2]) >= 2:
            pairs = keep_n_msb(rankset_of_count[2], 2)
            remaining = keep_n_msb(rankset ^ pairs, 1)
            self._evaluation = (Hand.TWO_PAIR << 26) | (pairs << 13) | remaining
        elif rankset_of_count[2] != 0:
            remaining = keep_n_msb(rankset_of_count[1], 3)
            self._evaluation = (
                (Hand.PAIR << 26) | (rankset_of_count[2] << 13) | remaining
            )
        else:
            self._evaluation = keep_n_msb(rankset, 5)
        self._hand_type = self._evaluation >> 26
        self._hand_distinguisher = self._evaluation & 0x3FFFFFF

        # Save local vars as fields
        # All Cards
        self._rankset = rankset
        self._rank_count = rank_count
        self._rankset_suit = rankset_suit
        self._rankset_of_count = rankset_of_count
        self._suit_count = suit_count
        # Hand
        self._hand_rankset = hand_rankset
        self._hand_rank_count = hand_rank_count
        self._hand_rankset_suit = hand_rankset_suit
        self._hand_rankset_of_count = hand_rankset_of_count
        self._hand_suit_count = hand_suit_count
        # Board
        self._board_rankset = board_rankset
        self._board_rank_count = board_rank_count
        self._board_rankset_suit = board_rankset_suit
        self._board_rankset_of_count = board_rankset_of_count
        return self._evaluation

    def get_rankset(self):
        self._evaluate_internal()
        return self._rankset

    def get_hand_rankset(self):
        self._evaluate_internal()
        return self._hand_rankset

    def get_board_rankset(self):
        self._evaluate_internal()
        return self._board_rankset

    def get_suit_count(self) -> Tuple[u32]:
        self._evaluate_internal()
        return tuple(self._suit_count)

    def get_hand_suit_count(self):
        self._evaluate_internal()
        return tuple(self._hand_suit_count)

    def get_board_suit_count(self):
        self._evaluate_internal()
        return tuple(self._board_suit_count)

    def get_suit_ranksets(self):
        self._evaluate_internal()
        return tuple(self._rankset_suit)


class ExtensiveHandDetails:
    def __init__(self, hand: Hand):
        self.hand = hand
        hand_cards = sorted(hand.hand_cards, reverse=True)
        board_cards = sorted(hand.board_cards, reverse=True)
        self.hand_ranks = [c // 4 for c in hand_cards]
        self.hand_suits = [c % 4 for c in hand_cards]
        self.board_ranks = [c // 4 for c in board_cards]
        self.board_suits = [c % 4 for c in board_cards]


class FlushDraws:
    def __init__(self):
        pass

    def categorize(self, hand: Hand) -> Tuple[str, int, int]:
        hand._suit_count
        pass


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
