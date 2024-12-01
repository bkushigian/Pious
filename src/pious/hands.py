"""
This module is responsible for various operations on NLHE hands, such as
categorization and ranking.
"""

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


def count_ones(x):
    # TODO: this is a very inefficient implementation
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
        self._rankset = u32(0)
        self._rank_count = u32(0)
        self._rankset_suit = u32(0)
        self._rankset_of_count = u32(0)
        self._extensive_details = None

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

    def _evaluate_internal(self):
        if self._evaluation != 0:
            # Cache the result
            return self._evaluation
        rankset = u32(0)
        rankset_suit = [u32(0), u32(0), u32(0), u32(0)]
        rankset_of_count = [u32(0), u32(0), u32(0), u32(0), u32(0)]
        rank_count = [u32(0) for _ in range(13)]
        for c in self.all_cards:
            r = u32(c // 4)
            s = u32(c % 4)
            rankset |= 1 << r
            rankset_suit[s] |= 1 << r
            rank_count[r] += 1

        for r in range(13):
            rankset_of_count[rank_count[r]] |= 1 << r

        flush_suit = u32(0xFFFFFFFF)
        for suit in range(4):
            if count_ones(rankset_suit[suit]) >= 5:
                flush_suit = suit
                break

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
        self._rankset = rankset
        self._rank_count = rank_count
        self._rankset_suit = rankset_suit
        self._rankset_of_count = rankset_of_count
        return self._evaluation


class ExtensiveHandDetails:
    def __init__(self, hand: Hand):
        self.hand = hand
        hand_cards = sorted(hand.hand_cards, reverse=True)
        board_cards = sorted(hand.board_cards, reverse=True)
        self.hand_ranks = [c // 4 for c in hand_cards]
        self.hand_suits = [c % 4 for c in hand_cards]
        self.board_ranks = [c // 4 for c in board_cards]
        self.board_suits = [c % 4 for c in board_cards]
