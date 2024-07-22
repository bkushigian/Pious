import pytest

from pious.pio.equity import EquityCalculator, compute_equities
from pious.pio.util import make_solver


def approx(x, tolerance=0.01):
    return pytest.approx(x, tolerance)


def test_equity_calc():
    ec = EquityCalculator("Kh9d8d", oop_range="AKo, 32o", ip_range="T9s, T8s")
    assert ec.oop() == approx(0.347)
    assert ec.ip() == approx(0.652)

    ec.set_board("3h3d3c")
    assert ec.oop() == approx(0.795)
    assert ec.ip() == approx(0.205)

    ec.set_oop_range("JJ, TT")
    ec.set_ip_range("AA, KK, QQ")

    assert ec.oop() == approx(0.088)
    assert ec.ip() == approx(0.912)
    assert ec.oop(preflop=True) == approx(0.186)
    assert ec.ip(preflop=True) == approx(0.813)

    assert compute_equities("3h3d3c", "JJ TT", "AA    KK,QQ") == (
        approx(0.088),
        approx(0.912),
    )
    assert compute_equities("3h3d3c", "JJ TT", "AA    KK,QQ", preflop=True) == (
        approx(0.186),
        approx(0.813),
    )
