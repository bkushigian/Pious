from typing import Dict
import pandas as pd
from os import path as osp
from io import StringIO

TEST_TREE = r"C:\PioSOLVER\Reports\SimpleTree\SRP\b25\BTNvBB"


ranks = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}


def card_tuple(c):
    r, s = c.strip()
    return ranks[r], s


class AggregationReport:
    def __init__(self, raw: str):
        lines = raw.splitlines()
        self.header = lines[:3]
        body = StringIO("\n".join(lines[3:]))
        df = pd.read_csv(body)
        df = df.drop(df.index[-1])
        self._df = df
        self._process_flops()
        self._compute_textures()

    def _process_flops(self):
        df = self._df
        df.rename(columns={"Flop": "RawFlop"}, inplace=True)
        flops_s = df["RawFlop"]
        flops_t = []

        for flop in flops_s:
            c1, c2, c3 = flop.split()
            flops_t.append((card_tuple(c1), card_tuple(c2), card_tuple(c3)))

        df["Flop"] = flops_t
        df.sort_values(by="Flop", ascending=False, inplace=True)

    def _compute_textures(self):
        df = self._df
        df["Pairedness"] = None
        df["Suitedness"] = None
        df["Connectedness"] = None
        for idx, row in df.iterrows():
            flop = row["Flop"]
            ranks = [c[0] for c in flop]
            suits = [c[1] for c in flop]

            # Pairedness
            pairedness = None
            n_ranks = len(set(ranks))
            if n_ranks == 3:
                pairedness = "UNPAIRED"
            elif n_ranks == 2:
                pairedness = "PAIRED"
            elif n_ranks == 1:
                pairedness = "TOAK"

            # Suitedness
            suitedness = None
            n_suits = len(set(suits))
            if n_suits == 3:
                suitedness = "RAINBOW"
            elif n_suits == 2:
                suitedness = "FD"
            elif n_suits == 1:
                suitedness = "MONOTONE"

            # Connectedness
            connectedness = "DISCONNECTED"
            has_ace = 14 in ranks
            # Check for straights
            if pairedness == "UNPAIRED":
                if max(ranks) - min(ranks) < 5:
                    connectedness = "STRAIGHT"
                elif has_ace:
                    if max([r % 14 for r in ranks]) <= 5:
                        connectedness = "STRAIGHT"
            # Else, check to see if straight draws are possible
            unique_ranks = list(set(ranks))
            if has_ace:
                unique_ranks.append(1)
            unique_ranks.sort(reverse=True)

            diffs = [
                abs(unique_ranks[i] - unique_ranks[i + 1])
                for i in range(len(unique_ranks) - 1)
            ]
            if len(diffs) > 0:
                diff = min(diffs)
                if diff <= 3:
                    connectedness = "OESD"
                elif diff == 4:
                    connectedness = "GUTSHOT"
            df.at[idx, "Pairedness"] = pairedness
            df.at[idx, "Suitedness"] = suitedness
            df.at[idx, "Connectedness"] = connectedness


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
            report_path = osp.join(self.path, "report.csv")
            if osp.exists(report_path):
                with open(report_path, "r") as f:
                    self._report = AggregationReport(f.read().strip())
        return self._report


class AggregationTreeViewer:
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

    with open(report_path, "r") as f:
        raw_report = f.read()

    agg_report = AggregationReport(raw_report)
    return agg_report


def test_aggregation_report():
    print("Testing aggregation reports")
    agg_report = get_test_report_r_x()
    print(agg_report._df)
    print("Done testing aggregation reports")


if __name__ == "__main__":
    test_aggregation_report()
