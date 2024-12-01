from pious.hands import hand


def test_hand_category():
    h = hand("3s3c", "8s6s5sAs")
    assert h.is_flush()
    assert not h.is_pair()
