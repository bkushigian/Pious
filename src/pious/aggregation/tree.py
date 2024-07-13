from os import path as osp
from typing import Dict
from pious.aggregation.report import AggregationReport
from pious.aggregation.util import *


class TreeNode:
    def __init__(self, path):
        """
        Args:
            path (str): file path to directory corresponding to node in agg tree
        """
        self.path = path
        self._children: Dict[str, TreeNode] = {}
        self._info = None
        self._report = None

    def __getitem__(self, item):
        return self._children.get(item, default=None)

    def get_info(self) -> str:
        """
        Get node info, if it exists. Otherwise return the empty string
        """
        if self._info is None:
            info_path = osp.join(self.path, "info.txt")
            self._info = ""
            if osp.exists(info_path):
                with open(info_path, "r") as f:
                    self._info = f.read().strip()
        return self._info

    def get_report(self) -> AggregationReport:
        if self._report is None:
            if osp.exists(self.path):
                self._report = AggregationReport(self.path)
        return self._report


class TreeViewer:
    """
    View and navigate a tree of aggregation reports.

    The base of the tree contains the Root directory, which corresponds to the
    root of the PIO tree.

    ```
    base/
      +-- Root/
            +-- Check/
            |      +-- Bet 11/
            |      |     +-- Call/
            |      |     +-- Fold/
            |      +-- Check/     # To the turn
            +-- Bet 11/
                  +-- Call/
                  +-- Fold/
                  +-- Raise/
                        +-- .../
    ```
    """

    def __init__(self, base: str):
        self.base = base
        self._path = []


def get_test_report_r_x():
    r = osp.join(TEST_TREE, "Root")
    r_x = osp.join(r, "CHECK")
    assert osp.isdir(r_x)

    report_path = osp.join(r_x, "report.csv")
    assert osp.isfile(report_path)
    agg_report = AggregationReport(r_x)
    return agg_report


def test_aggregation_report():
    print("Testing aggregation reports")
    agg_report = get_test_report_r_x()
    print(agg_report._df)
    print("Done testing aggregation reports")


if __name__ == "__main__":
    test_aggregation_report()
