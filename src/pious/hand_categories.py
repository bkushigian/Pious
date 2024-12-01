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
        return self.categories[hand._hand_type]
