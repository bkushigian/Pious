import pytest
from pious.flops import Flops


@pytest.fixture
def flops_obj():
    return Flops()


def test_flops_len(flops_obj):
    # Should return the number of flops in the view
    assert len(flops_obj) == len(flops_obj._df)


def test_flops_view_hidden_columns(flops_obj):
    # The view should not contain hidden columns
    view = flops_obj.view()
    for col in flops_obj.hidden_columns:
        assert col not in view.columns


def test_flops_filter(flops_obj):
    flops_obj.filter("r1 == 14")  # Only Ace-high flops
    # Check that all flops are ace-high
    assert all(flops_obj._df[["r1"]] == 14)


def test_flops_reset_and_filter(flops_obj):
    # Filtering should reduce the number of flops, reset should restore
    initial_len = len(flops_obj)
    initial_view = flops_obj.view()
    assert initial_len == 1755
    flops_obj.filter("r1 == 14")  # Only Ace-high flops
    filtered_len = len(flops_obj)
    assert filtered_len == 379
    flops_obj.reset()
    assert len(flops_obj) == 1755
    assert flops_obj.view().equals(initial_view)


def test_flops_filter_and_undo(flops_obj):
    initial_len = len(flops_obj)
    flops_obj.filter("r1 == 14")
    after_filter = len(flops_obj)
    flops_obj.filter("rainbow")
    flops_obj.undo_filter()
    assert len(flops_obj) == after_filter
    flops_obj.undo_filter()
    assert len(flops_obj) == initial_len


def test_flops_str_and_repr(flops_obj):
    flops_obj.filter("r1 == r2 == 14 and r3 == 13")
    s = str(flops_obj)
    assert s == "AdAhKc\nAcAdKc"
    assert isinstance(s, str)
    assert all(len(line) == 6 for line in s.splitlines())
    r = repr(flops_obj)
    assert r.startswith("<Flops:")
