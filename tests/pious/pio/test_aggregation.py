from pious.pio.aggregation import load_report_to_df, AggregationReport
from pious.pio.resources import get_database_root, get_aggregation_root


def test_aggregation_report():
    """
    This is a single huge aggregation report test. Should be broken up later
    """

    root_dir = get_aggregation_root()
    db_root = get_database_root()
    r = AggregationReport(root_dir, db_root)

    print(r.view())
    print(r.describe())

    assert len(r) == 7

    r.filter("r1 == 14")
    assert len(r) == 2
    r.reset("r1 == 13")
    assert len(r) == 2
    r.reset("r1 == 12")
    assert len(r) == 1
    r.reset()
    assert len(r) == 7

    # Test getitem
    assert r["As 9s 6h"].iloc[0]["raw_flop"] == "As 9s 6h"
    # Test for isomorphism resolution
    assert r["Ad 9d 6c"].iloc[0]["raw_flop"] == "As 9s 6h"

    # Check tree navigation and report caching
    assert len(r._report_cache) == 1, "Report caching error"
    r2 = r.take_action("CHECK")
    assert len(r2) == 7
    assert len(r._report_cache) == 2, "Report caching error"
    assert len(r2._report_cache) == 2, "Report caching error"
    r3 = r2.parent()
    assert r == r3, "Aggregation Report Caching has Failed "
    assert len(r._report_cache) == 2, "Report caching error"
    assert len(r2._report_cache) == 2, "Report caching error"
    assert len(r3._report_cache) == 2, "Report caching error"
