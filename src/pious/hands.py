"""
This module is responsible for various operations on NLHE hands, such as
categorization and ranking.
"""

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

        self._board_type = None

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

    def hand_type(self, adjust_for_board=False):
        if adjust_for_board:
            return self.board_adjusted_hand_type()
        return self._hand_type

    def board_adjusted_hand_type(self):

        bt = self._board_type
        ht = self._hand_type
        if bt > Hand.TRIPS:
            return ht  # In this case, we care about interaction
        elif self._board_type == Hand.TRIPS:
            if ht > Hand.TRIPS:
                return ht

            elif 2 in self._hand_rank_count:
                # Look for better trips
                n = 0
                for hrc, brc in zip(
                    self._hand_rank_count[::-1], self._board_rank_count[::-1]
                ):
                    if hrc == 2:
                        return Hand.TRIPS
                    elif brc == 3:
                        return Hand.HIGH_CARD
                raise RuntimeError("Illegal State: This should never be reached")
            return Hand.HIGH_CARD
        elif self._board_type == Hand.TWO_PAIR:
            if ht > Hand.TWO_PAIR:
                return ht
            elif 2 in self._hand_rank_count:
                # Check if we have a better 2 pair
                n = 0
                for hrc, brc in zip(
                    self._hand_rank_count[::-1], self._board_rank_count[::-1]
                ):
                    if hrc == 2:
                        return Hand.TWO_PAIR
                    elif brc == 2:
                        n += 1
                        if n >= 2:
                            return Hand.HIGH_CARD
                raise RuntimeError("Illegal State: This should never be reached")
        elif self._board_type == Hand.PAIR:
            if ht == Hand.TWO_PAIR:
                n = 0
                for hrc, brc in zip(
                    self._hand_rank_count[::-1], self._board_rank_count[::-1]
                ):
                    if hrc == 1 and brc == 1:
                        n += 1
                        if n == 2:
                            return Hand.TWO_PAIR
                    elif brc == 2 or hrc == 2:
                        return Hand.PAIR
                raise RuntimeError("Unreachable! The above loop should always return")
            elif ht == Hand.PAIR:
                return Hand.HIGH_CARD
        return ht

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

        try:
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
            return self._evaluation

        finally:
            # compute _board_type
            # Number of board rank counts for each possible rank count
            n_brcs = [0, 0, 0, 0, 0]
            self._board_type = Hand.HIGH_CARD
            for rc in board_rank_count:
                n_brcs[rc] += 1
            if n_brcs[4] >= 1:
                self._board_type = Hand.QUADS
            elif n_brcs[3] >= 1:
                if n_brcs[2] >= 1:
                    self._board_type = Hand.FULL_HOUSE
                else:
                    self._board_type = Hand.TRIPS
            elif n_brcs[2] == 2:
                self._board_type = Hand.TWO_PAIR
            elif n_brcs[2] == 1:
                self._board_type = Hand.PAIR
            elif len(self.board) == 5:
                ### Find straight flush on board
                if is_straight_flush:
                    board_suit_count = [0, 0, 0, 0]
                    board_flush_suit = u32(0xFFFFFFFF)
                    for suit in range(4):
                        c = count_ones(board_rankset_suit[suit])
                        board_suit_count[suit] = c
                        if c >= 5:
                            board_flush_suit = suit

                    if board_flush_suit < 4:
                        board_is_straight_flush = find_straight(
                            board_rankset_suit[board_flush_suit]
                        )
                        if board_is_straight_flush != 0:
                            self._board_type = Hand.STRAIGHT_FLUSH
                elif flush and 5 in board_suit_count:
                    self._board_type = Hand.FLUSH
                elif is_straight and find_straight(board_rankset):
                    self._board_type = Hand.STRAIGHT
            # Save local vars as fields
            # All Cards
            self._hand_type = self._evaluation >> 26
            self._hand_distinguisher = self._evaluation & 0x3FFFFFF
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

    def get_hand_suit_ranksets(self):
        self._evaluate_internal()
        return tuple(self._hand_rankset_suit)
