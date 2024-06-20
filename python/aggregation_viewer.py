from typing import Dict
import pandas as pd
from os import path as osp
from io import StringIO
from collections import namedtuple
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplcursors

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


def ahml(rank):
    if rank == 14:
        return "A"
    if rank > 9:
        return "H"
    if rank > 5:
        return "M"
    else:
        return "L"


def color_texture(texture):
    """
    Return a coloration of a texture
    """

    red = "00"
    green = "00"
    blue = "00"

    if "MONOTONE" in texture:
        red = "ff"
    elif "FD" in texture:
        red = "99"
    elif "RAINBOW" in texture:
        red = "00"
    else:
        print(f"Warning: Unrecognized suitedness {texture}")

    if "STRAIGHT" in texture:
        green = "ff"
    elif "OESD" in texture:
        green = "aa"
    elif "GUTSHOT" in texture:
        green = "55"
    elif "DISCONNECTED" in texture:
        green = "00"
    else:
        print(f"Warning: Unrecognized connectedness {texture}")

    if "TOAK" in texture:
        blue = "ff"
    elif "PAIRED" in texture:
        blue = "99"
    elif "UNPAIRED" in texture:
        blue = "00"
    else:
        print(f"Warning: Unrecognized pairedness {texture}")

    return f"#{red}{green}{blue}"


ranks_rev = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "T",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
}


def card_tuple(c):
    r, s = c.strip()
    return ranks[r], s


Info = namedtuple("Info", ["player", "node_id", "line", "starting_stacks"])


def parse_info(info: str):
    lines = info.splitlines()
    player = lines[0].strip().split()[0]
    node_id = lines[1][9:].strip()
    line = lines[3][6:].strip()
    starting_stacks = int(lines[4].split(":")[1].strip())
    return Info(player, node_id, line, starting_stacks)


class AggregationReport:
    def __init__(self, agg_report_directory: str):
        self.agg_report_directory = agg_report_directory
        self.csv_path = osp.join(agg_report_directory, "report.csv")
        self.info_path = osp.join(agg_report_directory, "info.txt")
        self.ip = False
        self.oop = False
        self.info = None
        self._df = None
        self._view: pd.DataFrame = None
        self.columns_to_suppress = []
        self.column_filters = []
        self.load_info()
        self.load_from_csv()
        self._default_column_filters()

        # We keep track of the current _view_ of the aggregation report, which
        # allows us to make modifications (e.g., through filters, sorting, etc)
        # without modifying the original
        self.reset()

    def load_from_csv(self):
        """
        Load the dataframe from the raw csv passed in.
        """
        with open(self.csv_path) as f:
            lines = f.readlines()
        self.header = lines[:3]
        self.body = StringIO("\n".join(lines[3:]))
        df = pd.read_csv(self.body)
        df = df.drop(df.index[-1])
        self._df = df
        self.clean_column_names()
        self._process_flops()
        self._compute_textures()
        self._view = self._df.copy()
        return self._view

    def load_info(self):
        with open(self.info_path) as f:
            info_text = f.read()
        self.info = parse_info(info_text)
        if self.info.player == "OOP":
            self.oop = True
        elif self.info.player == "IP":
            self.ip = True
        else:
            raise RuntimeError("Unknown Player", self.info.player)

    def clean_column_names(self):
        us = "ip" if self.ip else "oop"
        new_names = {}
        for column in self._df.columns:
            new_name = column.lower()
            if new_name.startswith(us + " "):
                new_name = new_name[len(us) + 1 :].replace(" ", "_")
                new_names[column] = new_name
            elif new_name.endswith(" freq"):
                new_name = new_name[:-5]
            elif new_name == "global %":
                new_name = "global_freq"
            if " " in new_name:
                new_name = new_name.replace(" ", "_")
            new_names[column] = new_name.replace(" ", "_")
        self._df.rename(columns=new_names, inplace=True)

    def _default_column_filters(self):
        other_player = "ip" if self.oop else "oop"
        columns_to_suppress = [
            "global_freq",
            "flop",
            "pairedness",
            "suitedness",
            "connectedness",
            "ahml",
            "high_card",
        ]
        for col in self.columns():
            if col.startswith(other_player):
                columns_to_suppress.append(col)
        self.columns_to_suppress = columns_to_suppress

    def view(self) -> pd.DataFrame:
        """
        There are some things we need to do before showing the view. For
        instance, we don't want to show all of the book-keeping (the Flop
        column, the Id column, the other player's EV/Equity/EQR, etc).

        This does some final transformations on the view before returning it,
        leaving the actual view unchanged.
        """

        result = self._view.copy()
        to_drop = [c for c in self.columns_to_suppress if c in result]
        result.drop(columns=to_drop, inplace=True)
        return result

    def reset(self):
        """
        Reset the view
        """
        self._view = self._df.copy()
        return self

    def sort_by(self, by, ascending=True):
        """
        Sort the current view by columns
        """
        self._view.sort_values(by=by, ascending=ascending, inplace=True)
        return self

    def filter(self, query_string):
        self._view.query(expr=query_string, inplace=True)
        return self

    def filter_texture(self, textures=None, pred=None):
        v = self._view
        if textures is not None:

            def fn(tup):
                for t in textures:
                    if t.upper() not in tup:
                        return False
                return True

            v = v[v["texture"].apply(fn)]
        if pred is not None:
            v = v[v["texture"].apply(pred)]

        self._view = v
        return self

    def columns(self):
        return self._view.columns

    def head(self, n=10):
        self._view = self._view.head(n)
        return self

    def tail(self, n=10):
        self._view = self._view.tail(n)
        return self

    def plot(self, columns=None, labels=True):
        v = self.view()
        fig, ax = plt.subplots()
        colors = [color_texture(texture) for texture in v["texture"]]
        if columns is None:
            columns = ["ev", "ev"]
        if len(columns) == 1:
            c1 = columns[0]
            c2 = c1
        elif len(columns) == 2:
            c1, c2 = columns
        else:
            c1, c2 = "ev", "ev"
        scatter = ax.scatter(
            v[c1], v[c2], c=colors, label=v["raw_flop"], s=60, edgecolors="black"
        )
        all_textures = [
            ("3 of a kind", ("TOAK", "RAINBOW", "DISCONNECTED")),
            ("monotone disconneted", ("UNPAIRED", "MONOTONE", "DISCONNECTED")),
            ("monotone connected", ("UNPAIRED", "MONOTONE", "STRAIGHT")),
            ("monotone gutshot", ("UNPAIRED", "MONOTONE", "GUTSHOT")),
            ("monotone oesd", ("UNPAIRED", "MONOTONE", "OESD")),
            ("rainbow disconnected", ("UNPAIRED", "RAINBOW", "DISCONNECTED")),
            ("rainbow connected", ("UNPAIRED", "RAINBOW", "STRAIGHT")),
            ("rainbow oesd", ("UNPAIRED", "RAINBOW", "OESD")),
            ("rainbow gutter", ("UNPAIRED", "RAINBOW", "GUTSHOT")),
            ("flushdraw disconnected", ("UNPAIRED", "FD", "DISCONNECTED")),
            ("flushdraw connected", ("UNPAIRED", "FD", "STRAIGHT")),
            ("flushdraw oesd", ("UNPAIRED", "FD", "OESD")),
            ("flushdraw gutter", ("UNPAIRED", "FD", "GUTSHOT")),
            ("paired rainbow disconnected", ("PAIRED", "RAINBOW", "DISCONNECTED")),
            ("paired rainbow oesd", ("PAIRED", "RAINBOW", "OESD")),
            ("paired rainbow gutter", ("PAIRED", "RAINBOW", "GUTSHOT")),
            ("paired flushdraw disconnected", ("PAIRED", "FD", "DISCONNECTED")),
            ("paired flushdraw oesd", ("PAIRED", "FD", "OESD")),
            ("paired flushdraw gutter", ("PAIRED", "FD", "GUTSHOT")),
        ]
        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label=label,
                markerfacecolor=color_texture(t),
                markersize=8,
            )
            for (label, t) in all_textures
        ]
        # Add the legend
        ax.legend(handles=legend_elements, loc="upper left", prop={"size": 15})

        mplcursors.cursor(ax.collections, hover=True).connect(
            "add",
            lambda sel: sel.annotation.set_text(v["raw_flop"].iloc[sel.index]),
        )
        ax.set_xlabel(c1, fontsize=15)
        ax.set_ylabel(c2, fontsize=15)
        ax.set_title(
            f"{c1.capitalize()} vs {c2.capitalize()}".replace("_", " "), fontsize=20
        )
        plt.show()

    def _process_flops(self):
        df = self._df
        df.rename(columns={"flop": "raw_flop"}, inplace=True)
        flops_s = df["raw_flop"]
        flops_t = []

        for flop in flops_s:
            c1, c2, c3 = flop.split()
            flops_t.append((card_tuple(c1), card_tuple(c2), card_tuple(c3)))

        df["flop"] = flops_t
        df.sort_values(by="flop", ascending=False, inplace=True)

    def _compute_textures(self):
        df = self._df
        df["pairedness"] = None
        df["suitedness"] = None
        df["connectedness"] = None
        df["high_card"] = None
        df["ahml"] = None
        df["texture"] = None
        for idx, row in df.iterrows():
            flop = row["flop"]
            ranks = [c[0] for c in flop]
            suits = [c[1] for c in flop]

            # High card
            high_card = ranks_rev[max(ranks)] + "_high"

            # AHML
            ahml_label = "".join([ahml(r) for r in ranks])

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
            if connectedness == "DISCONNECTED":
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
            df.at[idx, "pairedness"] = pairedness
            df.at[idx, "suitedness"] = suitedness
            df.at[idx, "connectedness"] = connectedness
            df.at[idx, "ahml"] = ahml_label
            df.at[idx, "high_card"] = high_card
            df.at[idx, "texture"] = (
                high_card,
                pairedness,
                suitedness,
                connectedness,
                ahml_label,
            )

    def get_actions(self):
        columns = self._df.columns
        keys = ("bet", "check", "call", "raise", "fold")
        actions = []
        for c in columns:
            for key in keys:
                if c.lower().startswith(key):
                    actions.append(c)
                    break
        return actions

    def __str__(self):
        view = self.view()
        view_str = str(view)
        return view_str

    def __repr__(self):
        return str(self)


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
    agg_report = AggregationReport(r_x)
    return agg_report


def test_aggregation_report():
    print("Testing aggregation reports")
    agg_report = get_test_report_r_x()
    print(agg_report._df)
    print("Done testing aggregation reports")


if __name__ == "__main__":
    test_aggregation_report()
