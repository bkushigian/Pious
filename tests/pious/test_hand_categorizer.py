from pious.hands import Hand
from pious.hand_categories import HandCategorizer


def test_pair_types_on_paired_board():
    h = Hand("AhAc", "Th2c2d")
    assert HandCategorizer.categorize(h) == HandCategorizer.categories[Hand.TWO_PAIR]
    t, s, k = HandCategorizer.get_pair_category(h)
    assert t == HandCategorizer.POCKET_PAIR
    assert s == 0
    assert k == 0

    h = Hand("AhTc", "Th2c2d")
    assert HandCategorizer.categorize(h) == HandCategorizer.categories[Hand.TWO_PAIR]
    t, s, k = HandCategorizer.get_pair_category(h)
    assert t == HandCategorizer.REGULAR_PAIR
    assert s == 1
    assert k == 1

    h = Hand("KhTc", "Th2c2d")
    assert HandCategorizer.categorize(h) == HandCategorizer.categories[Hand.TWO_PAIR]
    t, s, k = HandCategorizer.get_pair_category(h)
    assert t == HandCategorizer.REGULAR_PAIR
    assert s == 1
    assert k == 2


def test_pair_types_on_toak_board():
    h = Hand("AhAc", "2h2c2d")
    assert HandCategorizer.categorize(h) == HandCategorizer.categories[Hand.FULL_HOUSE]
    t, s, k = HandCategorizer.get_pair_category(h)
    assert t == HandCategorizer.POCKET_PAIR
    assert s == 0
    assert k == 0
