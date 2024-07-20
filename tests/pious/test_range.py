from pious.range import Range


def test_range_constructor():
    r = Range("AA")
    assert r["AsAh"] == 1.0
    assert r["AhAs"] == 1.0
    assert r["AsAd"] == 1.0
    assert r["AdAs"] == 1.0
    assert r["AsAc"] == 1.0
    assert r["AcAs"] == 1.0
    assert r["AhAd"] == 1.0
    assert r["AdAh"] == 1.0
    assert r["AhAc"] == 1.0
    assert r["AcAh"] == 1.0
    assert r["AdAc"] == 1.0
    assert r["AcAd"] == 1.0

    assert r["AdKs"] == 0.0
    assert r["KdKs"] == 0.0


def test_range_setitem():
    r = Range("")
    assert r["AsAh"] == 0.0
    assert r["AhAs"] == 0.0
    assert r["AsAd"] == 0.0
    assert r["AdAs"] == 0.0
    assert r["AsAc"] == 0.0
    assert r["AcAs"] == 0.0
    assert r["AhAd"] == 0.0
    assert r["AdAh"] == 0.0
    assert r["AhAc"] == 0.0
    assert r["AcAh"] == 0.0
    assert r["AdAc"] == 0.0
    assert r["AcAd"] == 0.0

    assert r["AdKs"] == 0.0
    assert r["KdKs"] == 0.0

    r["AhAd"] = 0.2

    assert r["AsAh"] == 0.0
    assert r["AhAs"] == 0.0
    assert r["AsAd"] == 0.0
    assert r["AdAs"] == 0.0
    assert r["AsAc"] == 0.0
    assert r["AcAs"] == 0.0
    assert r["AhAd"] == 0.2  # Updated
    assert r["AdAh"] == 0.2  # Updated
    assert r["AhAc"] == 0.0
    assert r["AcAh"] == 0.0
    assert r["AdAc"] == 0.0
    assert r["AcAd"] == 0.0

    assert r["AdKs"] == 0.0
    assert r["KdKs"] == 0.0

    r["AA"] = 1.0
    assert r["AA"] == 1.0

    assert r["AsAh"] == 1.0
    assert r["AhAs"] == 1.0
    assert r["AsAd"] == 1.0
    assert r["AdAs"] == 1.0
    assert r["AsAc"] == 1.0
    assert r["AcAs"] == 1.0
    assert r["AhAd"] == 1.0
    assert r["AdAh"] == 1.0
    assert r["AhAc"] == 1.0
    assert r["AcAh"] == 1.0
    assert r["AdAc"] == 1.0
    assert r["AcAd"] == 1.0

    assert r["AdKs"] == 0.0
    assert r["KdKs"] == 0.0

    r["AKo"] = 1.0
    assert r["AdKs"] == 1.0
    assert r["AsKd"] == 1.0
    assert r["AhKc"] == 1.0
    assert r["AhKh"] == 0.0

    r = Range("AA:0.5,KK:0.25")
    assert r["AA"] == 0.5
    assert r["KK"] == 0.25
    assert r["KhKd"] == 0.25


def test_num_combos():
    r = Range("AA")
    assert 6.0 == r.num_combos()

    r = Range("AA,TT, QQ")
    assert 18.0 == r.num_combos()

    r = Range("AA:0.5,TT:0.5")
    assert 6.0 == r.num_combos()
