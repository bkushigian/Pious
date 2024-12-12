from pious.hands import hand, Hand, StraightDrawMasks

masks = StraightDrawMasks()


def straight_draw_type(hole, board):
    return masks.categorize(hand(hole, board))


def test_hand_category():
    h = hand("3s3c", "8s6s5sAs")
    assert h.is_flush()
    assert not h.is_pair()
    assert not h.is_straight()

    h = hand("3d3c", "8s6s5sAs")
    assert not h.is_flush()
    assert h.is_pair()
    assert not h.is_straight()


def test_straight_draw_masks_a_high_broadway():

    assert straight_draw_type("AsTd", "JhKh3d") == ("A_HIGH_BROADWAY", 2)
    assert straight_draw_type("AsTd", "JhKhTd") == ("A_HIGH_BROADWAY", 1)
    assert straight_draw_type("AsKd", "JhQh9d") == ("A_HIGH_BROADWAY", 2)


def test_straight_draw_masks_a_high_wheel():

    assert straight_draw_type("AsTd", "2h3h4d") == ("A_HIGH_WHEEL", 1)
    assert straight_draw_type("As2d", "Jh4h3d") == ("A_HIGH_WHEEL", 2)


def test_straight_draw_masks_oesd():
    assert straight_draw_type("KsQs", "JhTh8h7h6d") == ("OESD", 2)
    assert straight_draw_type("KsJh", "QdJcTh8h") == ("OESD", 1)
    assert straight_draw_type("QsJh", "KdJcTh8h") == ("OESD", 1)
    assert straight_draw_type("JhTh", "JsTd9d8s") == ("NO_STRAIGHT_DRAW", 0)


def test_straight_draw_masks_double_gutters():
    ## 1011101
    assert straight_draw_type("AsKs", "JsTh9d7h") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("AsKs", "JsTh9d7h") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("KsQs", "Th9d8h6d") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("8s6s", "KhQdTh9d") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("QsQc", "Th9d8h6d") == ("DOUBLE_GUTTER", 1)
    assert straight_draw_type("QsTc", "Th9d8h6d") == ("DOUBLE_GUTTER", 1)
    assert straight_draw_type("Qs9c", "Th9d8h6d") == ("DOUBLE_GUTTER", 1)
    assert straight_draw_type("Qs9c", "Th8h6d5s") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("Qs8c", "Th9h6d5s") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("QsJs", "9h8d7h5d") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("JhJs", "9h8d7h5d") == ("DOUBLE_GUTTER", 1)
    assert straight_draw_type("Jh9s", "9h8d7h5d") == ("DOUBLE_GUTTER", 1)
    assert straight_draw_type("Jh8s", "9h8d7h5d") == ("DOUBLE_GUTTER", 1)
    assert straight_draw_type("Jh8s", "9h7h5d4s") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("JsTs", "8d7h6d4s") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("Ts9s", "7h6d5d3s") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("9s8s", "6h5d4d2s") == ("DOUBLE_GUTTER", 2)
    ## 11011011
    assert straight_draw_type("AsKs", "JcTh8d7h") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("KsQs", "Th9d7h6c") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("QsJs", "9d8h6c5d") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("JsTs", "8h7d5d4c") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("Ts9d", "7d6h4c3d") == ("DOUBLE_GUTTER", 2)
    assert straight_draw_type("Ts9d", "7d6h4c3d") == ("DOUBLE_GUTTER", 2)


def test_straight_draw_masks_gutshots():
    assert straight_draw_type("KsQs", "Th9d7h") == ("GUTSHOT", 2)
    assert straight_draw_type("KsJs", "Th9d6h") == ("GUTSHOT", 2)
    assert straight_draw_type("KsJs", "Th9d6hJd") == ("GUTSHOT", 1)
    assert straight_draw_type("KsJs", "Th9d6hKd") == ("GUTSHOT", 1)


def test_straight_draw_masks_backdoor():
    assert straight_draw_type("KsQs", "Th3d2h") == ("BACKDOOR_STRAIGHT_DRAW", 2)
    assert straight_draw_type("KsQs", "Jh3d2h") == ("BACKDOOR_STRAIGHT_DRAW", 2)
    assert straight_draw_type("Ks5s", "Jh3d2h") == ("BACKDOOR_STRAIGHT_DRAW", 1)
    assert straight_draw_type("7s6s", "9h3d2h") == ("BACKDOOR_STRAIGHT_DRAW", 2)

    # 4 high/5 high
    assert straight_draw_type("Ks2s", "9h4d3h") == ("BACKDOOR_STRAIGHT_DRAW", 1)
    assert straight_draw_type("Ks2s", "9h5d3h") == ("BACKDOOR_STRAIGHT_DRAW", 1)
    assert straight_draw_type("4s2s", "9h8d3h") == ("BACKDOOR_STRAIGHT_DRAW", 2)
    assert straight_draw_type("5s2s", "Th9d3h") == ("BACKDOOR_STRAIGHT_DRAW", 2)
    assert straight_draw_type("5s4s", "Th9d3h") == ("BACKDOOR_STRAIGHT_DRAW", 2)
    assert straight_draw_type("5s4s", "Th9d2h") == ("BACKDOOR_STRAIGHT_DRAW", 2)
    assert straight_draw_type("4s3s", "Th9d2h") == ("BACKDOOR_STRAIGHT_DRAW", 2)

    # Wheel backdoor draws
    assert straight_draw_type("AsQs", "9h3d2h") == ("BACKDOOR_WHEEL_DRAW", 1)
    assert straight_draw_type("As2s", "Th3d2h") == ("BACKDOOR_WHEEL_DRAW", 1)
    assert straight_draw_type("As2s", "Th3d9h") == ("BACKDOOR_WHEEL_DRAW", 2)
    assert straight_draw_type("3s2s", "Ah3d9h") == ("BACKDOOR_WHEEL_DRAW", 1)
    assert straight_draw_type("4s3s", "Ah9d9h") == ("BACKDOOR_WHEEL_DRAW", 2)
