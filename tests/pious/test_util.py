from pious.util import (
    NUM_COMBOS,
    ALL_COMBOS,
    OFFSUIT_COMBO_SUITS,
    SUITED_COMBO_SUITS,
    POCKET_PAIR_COMBO_SUITS,
    canonicalize_full_combo,
    full_combo_to_preflop_combo,
    preflop_combo_to_full_combos,
    is_full_combo,
    is_preflop_combo,
    get_pio_combo_index,
)


def test_all_combos():
    assert NUM_COMBOS == len(ALL_COMBOS)


def test_constants():
    assert 12 == len(OFFSUIT_COMBO_SUITS)
    assert 6 == len(POCKET_PAIR_COMBO_SUITS)
    assert 4 == len(SUITED_COMBO_SUITS)


def test_full_combo_to_preflop_combo():
    assert "ATo" == full_combo_to_preflop_combo("AhTd")
    assert "ATs" == full_combo_to_preflop_combo("AhTh")
    assert "ATs" == full_combo_to_preflop_combo("AdTd")
    assert "AA" == full_combo_to_preflop_combo("AdAc")


def test_preflop_combo_to_full_combo():
    assert (
        "AsTh",
        "AsTd",
        "AsTc",
        "AhTs",
        "AhTd",
        "AhTc",
        "AdTs",
        "AdTh",
        "AdTc",
        "AcTs",
        "AcTh",
        "AcTd",
    ) == preflop_combo_to_full_combos("ATo")


def test_all_full_combo_to_preflop_combo():
    for combo in ALL_COMBOS:
        # Map the combo to preflop combo, and then back to full combos

        combos = preflop_combo_to_full_combos(full_combo_to_preflop_combo(combo))
        canonical = canonicalize_full_combo(combo)
        assert canonical in combos


def test_is_preflop_combo():
    assert is_preflop_combo("ATo")
    assert is_preflop_combo("ATs")
    assert is_preflop_combo("AA")
    assert is_preflop_combo("JJ")
    assert is_preflop_combo("TT")
    assert not is_preflop_combo("TTs")
    assert not is_preflop_combo("TTo")
    assert not is_preflop_combo("AT")
    assert not is_preflop_combo("")
    assert not is_preflop_combo("")
    assert not is_preflop_combo("AhTd")


def test_is_full_combo():
    assert is_full_combo("AdTh")
    assert is_full_combo("AhTd")
    assert is_full_combo("AhAd")
    assert is_full_combo("AdAh")
    assert not is_full_combo("AdAd")
    assert not is_full_combo("AdA")
    assert not is_full_combo("AA")
    assert not is_full_combo("AAo")
    assert not is_full_combo("")


def test_get_pio_combo_index():
    assert get_pio_combo_index("AhAd") == get_pio_combo_index("AdAh")
    assert get_pio_combo_index("Ah9d") == get_pio_combo_index("9dAh")
    assert get_pio_combo_index("Ah9d") != get_pio_combo_index("9dAs")
