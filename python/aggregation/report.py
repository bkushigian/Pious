from typing import Dict, Optional
import pandas as pd
from os import path as osp
from io import StringIO
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplcursors
import webbrowser
import tempfile
import pydoc
from aggregation.util import *


class AggregationReport:
    def __init__(self, agg_report_directory: str, db_loc: Optional[str] = None):
        """Create a new `AggregationReport`

        Args:
            agg_report_directory (str): the location of the directory
            containing the aggregation report

            db_loc (Optional[str], optional): _description_. Defaults to None.
            the location of the database of solves that were used to generate
            the aggregation report
        """
        self.agg_report_directory = agg_report_directory
        self.csv_path = osp.join(agg_report_directory, "report.csv")
        self.info_path = osp.join(agg_report_directory, "info.txt")
        self.ip = False
        self.oop = False
        self.info = None
        self.plotter = Plotter(self)
        self._df = None
        self._view: pd.DataFrame = None
        self._current_filters = []
        self.hidden_columns = []
        self._load_info()
        self.load_from_csv()
        self.set_default_hidden_columns()

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
        self._clean_column_names()
        self._process_flops()
        self._compute_textures()
        self._view = self._df.copy()
        return self._view

    def view(self) -> pd.DataFrame:
        """
        There are some things we need to do before showing the view. For
        instance, we don't want to show all of the book-keeping (the Flop
        column, the Id column, the other player's EV/Equity/EQR, etc).

        This does some final transformations on the view before returning it,
        leaving the actual view unchanged.
        """

        result = self._view.copy()
        to_drop = [c for c in self.hidden_columns if c in result]
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
        """
        Filter the boards by some criterion.

        ## Example

        To filter all ace high boards without flushes, straights, or paired
        cards, you could issue the following query:

        ```
        r.filter("r1 == 14 and not flush and not straight and unpaired")
        ```
        """
        self._current_filters.append(query_string)
        self._view.query(expr=query_string, inplace=True)
        return self

    def undo_filter(self, n=1):
        """
        Remove the last n filters from the view
        """
        if n <= 0:
            return
        cf = self._current_filters[:-n]
        self.reset()
        for f in cf:
            self.filter(f)
        self._current_filters = cf

    def all_columns(self):
        """
        Return all columns in the `self._view` dataframe. This includes many
        columns that are hidden by default, but that are useful for issuing
        filters.
        """
        return self._view.columns

    def view_columns(self):
        """
        Return all columns in a `self.view()` result. This does not display any
        hidden columns that are in `self._view`.
        """
        return self.view().columns

    def head(self, n=10):
        self._view = self._view.head(n)
        return self

    def tail(self, n=10):
        self._view = self._view.tail(n)
        return self

    def in_browser(self):
        """
        Open the dataframe in a browser
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as f:
            url = "file://" + f.name
            html = self.view().to_html()
            f.write(html)
        webbrowser.open(url)

    def plot(
        self,
        col1=None,
        col2=None,
        min_size=None,
        max_size=None,
        labels=None,
        marker=None,
        sort_single_column=None,
        legend=None,
        legend_size=None,
    ):
        self.plotter.scatter(
            col1=col1,
            col2=col2,
            min_size=min_size,
            max_size=max_size,
            labels=labels,
            marker=marker,
            sort_single_column=sort_single_column,
            legend=legend,
            legend_size=legend_size,
        )

    def _find_matching_column(self, columns, column):
        if column in columns:
            return column
        if column is None:
            return None
        if columns is None:
            return None
        matches = [c for c in columns if c.startswith(column)]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            return None
        print(f"Column name {column} has multiple matches: {', '.join(matches)}")
        return None

    def set_default_hidden_columns(self):
        other_player = "ip" if self.oop else "oop"
        columns_to_suppress = [
            "global_freq",
            "flop",
            "pairedness",
            "suitedness",
            "connectedness",
            "ahml",
            "high_card",
            "r1",
            "r2",
            "r3",
            "s1",
            "s2",
            "s3",
            "flush",
            "flushdraw",
            "rainbow",
            "straight",
            "oesd",
            "gutshot",
            "straightdraw",
            "wheeldraw",
            "broadwaydraw",
            "disconnected",
            "toak",
            "paired",
            "unpaired",
            "wheel",
            "broadway",
        ]
        for col in self.all_columns():
            if col.startswith(other_player):
                columns_to_suppress.append(col)
        self.hidden_columns = columns_to_suppress

    def _load_info(self):
        with open(self.info_path) as f:
            info_text = f.read()
        self.info = parse_info(info_text)
        if self.info.player == "OOP":
            self.oop = True
        elif self.info.player == "IP":
            self.ip = True
        else:
            raise RuntimeError("Unknown Player", self.info.player)

    def _clean_column_names(self):
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

    def _process_flops(self):
        """
        An initial modification of the base dataframe: this should only be run
        once. This cleans up some data to ensure that flops are ordered
        correctly, ranks and suits are easily accessible, etc.
        """
        df = self._df
        df.rename(columns={"flop": "raw_flop"}, inplace=True)
        flops_s = df["raw_flop"]
        flops_t = []
        rs1, rs2, rs3, ss1, ss2, ss3 = [], [], [], [], [], []
        for flop in flops_s:
            c1, c2, c3 = flop.split()
            r1, s1 = card_tuple(c1)
            r2, s2 = card_tuple(c2)
            r3, s3 = card_tuple(c3)
            rs1.append(r1)
            ss1.append(s1)
            rs2.append(r2)
            ss2.append(s2)
            rs3.append(r3)
            ss3.append(s3)

            flops_t.append(((r1, r2, r3), (s1, s2, s3)))

        df["r1"] = rs1
        df["r2"] = rs2
        df["r3"] = rs3
        df["s1"] = ss1
        df["s2"] = ss2
        df["s3"] = ss3
        df["flop"] = flops_t
        df.sort_values(by="flop", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)

    def _compute_textures(self):
        """
        Compute texture columns
        """
        df = self._df
        df["pairedness"] = None
        df["suitedness"] = None
        df["connectedness"] = None
        df["high_card"] = None
        df["ahml"] = None

        df["texture"] = None

        df["flush"] = False
        df["flushdraw"] = False
        df["rainbow"] = False

        df["straight"] = False
        df["oesd"] = False
        df["gutshot"] = False
        df["straightdraw"] = False
        df["disconnected"] = False
        df["wheeldraw"] = False
        df["broadwaydraw"] = False

        df["toak"] = False
        df["paired"] = False
        df["unpaired"] = False

        df["wheel"] = False
        df["broadway"] = False

        for idx, row in df.iterrows():
            flop = row["flop"]
            ranks, suits = flop
            modulo_ranks = [r % 14 for r in ranks]

            # High card
            high_card = ranks_rev[max(ranks)] + "_high"

            # AHML
            ahml_label = "".join([ahml(r) for r in ranks])

            # Pairedness
            pairedness = None
            n_ranks = len(set(ranks))
            if n_ranks == 3:
                pairedness = "UNPAIRED"
                df.at[idx, "unpaired"] = True
            elif n_ranks == 2:
                pairedness = "PAIRED"
                df.at[idx, "paired"] = True
            elif n_ranks == 1:
                pairedness = "TOAK"
                df.at[idx, "toak"] = True

            # Suitedness
            suitedness = None
            n_suits = len(set(suits))
            if n_suits == 3:
                suitedness = "RAINBOW"
                df.at[idx, "rainbow"] = True
            elif n_suits == 2:
                suitedness = "FD"
                df.at[idx, "flushdraw"] = True
            elif n_suits == 1:
                suitedness = "MONOTONE"
                df.at[idx, "flush"] = True

            # Connectedness
            connectedness = "DISCONNECTED"
            has_ace = 14 in ranks
            # Check for straights
            if pairedness == "UNPAIRED":
                if max(ranks) - min(ranks) < 5:
                    connectedness = "STRAIGHT"
                    df.at[idx, "straight"] = True
                elif has_ace and max([r % 14 for r in ranks]) <= 5:
                    connectedness = "STRAIGHT"
                    df.at[idx, "straight"] = True
                    # Check if is broadway straight or wheel straight
                    if all([r >= 10 for r in ranks]):
                        df.at[idx, "broadway"] = True
                    if all([r <= 5 for r in modulo_ranks]):
                        df.at[idx, "wheel"] = True

            if connectedness == "DISCONNECTED":
                straightdraw = False
                # Else, check to see if straight draws are possible
                unique_ranks = list(set(ranks))
                if has_ace:
                    unique_ranks.append(1)
                unique_ranks.sort(reverse=True)
                for i in range(len(unique_ranks) - 1):
                    if connectedness == "OESD":  # We've already found an OESD
                        break
                    r1, r2 = unique_ranks[i : i + 2]
                    if 0 < r1 - r2 <= 3:
                        # If cards are close (e.g., 5h 8d), this makes for an
                        # open ended straight draw EXCEPT for when one of the
                        # cards is an ace
                        if r1 == 14:
                            connectedness = "GUTSHOT"
                            df.at[idx, "broadwaydraw"] = True
                            df.at[idx, "straightdraw"] = True
                        if r2 == 1:
                            connectedness = "GUTSHOT"
                            df.at[idx, "wheeldraw"] = True
                            df.at[idx, "straightdraw"] = True
                        else:
                            connectedness = "OESD"
                            df.at[idx, "oesd"] = True
                            df.at[idx, "gutshot"] = True
                            df.at[idx, "straightdraw"] = True
                    elif 0 < r1 - r2 == 4:
                        connectedness = "GUTSHOT"
                        df.at[idx, "gutshot"] = True
                        df.at[idx, "straightdraw"] = True

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

    def dump(self) -> str:
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        s = str(self.view())
        pd.reset_option("display.max_rows")
        pd.reset_option("display.max_columns")
        pd.reset_option("display.width")
        return s

    def paginate(self):
        pydoc.pager(self.dump())


class Plotter:
    def __init__(self, report: AggregationReport):
        self.report: AggregationReport = report
        self.min_size = 20
        self.max_size = 200
        self.labels = True
        self.marker = "o"
        self.legend = True
        self.legend_size = 12
        self.sort_single_column = False

    def scatter(
        self,
        col1=None,
        col2=None,
        labels=None,
        min_size=None,
        max_size=None,
        marker=None,
        sort_single_column=None,
        legend=True,
        legend_size=None,
    ):
        """
        This is a gargantuan method and should be refactored. I'm exploring
        different ideas at the moment and getting familiar with MPL. I should
        add an `AggregationReportPlotter` class and factor out this logic, along
        with a lot of settings/etc, to that.

        Currently: by default, if no columns are provided `plot()` will plot
        `ev` against an action. It tries to find the first interesting action,
        looking for bets, raises, calls, and then finally check.

        If a single column is provided it will plot the values from that column
        against the index of each value (0...N-1). The plotted column will be in
        sorted order if `sort_single_column` is `True`.

        If both columns are provided, plot col1 and col2 against each other.
        """
        report = self.report
        v: pd.DataFrame = report._view.copy()
        columns = list(v.columns)
        col1 = report._find_matching_column(columns, col1)
        col2 = report._find_matching_column(columns, col2)
        values1 = None
        values2 = None

        # Handle default values. We use the semantics of `or`, which returns the
        # first value with true truthiness, or the last value otherwise. This means that
        # `False or 7` evaluates to 7, while `100 or 7` evaluates to 100
        labels = labels or self.labels
        min_size = min_size or self.min_size
        max_size = max_size or self.max_size
        marker = marker or self.marker
        legend = legend or self.legend
        legend_size = legend_size or self.legend_size
        sort_single_column = sort_single_column or self.sort_single_column

        if min_size is None:
            min_size = 10
            if max_size is not None and min_size > max_size:
                max_size = min_size
        if max_size is None:
            max_size = 200
            if min_size > max_size:
                min_size = max_size

        # The following logic isn't great, but here we are :). I'll clean it up
        # at some point (regarding what to do when one column is None, both are
        # None, etc)
        if col1 is not None and col2 is None:
            if sort_single_column:
                v.sort_values(by=col1, ascending=True, inplace=True)
            values2 = v[col1]
            values1 = list(range(len(values2)))
            x_axis = "#"
            y_axis = col1
            if marker is None:
                marker = "."
        elif col1 is None and col2 is not None:
            if sort_single_column:
                v.sort_values(by=col2, ascending=True, inplace=True)
            values2 = v[col2]
            values1 = list(range(len(values2)))
            x_axis = "#"
            y_axis = col2
            if marker is None:
                marker = "."

        elif col1 is None and col2 is None:
            # By default, plot ev against the first action
            col1 = "ev"
            action_types = ("bet", "raise", "call")
            actions = report.get_actions()
            for prefix in action_types:
                xs = [a for a in actions if a.startswith(prefix)]
                if len(xs) > 0:
                    col2 = xs[0]
                    break
            if col2 is None:
                if "check" not in actions:
                    raise RuntimeError(f"No valid actions in {actions}")
                col2 = "check"
            values1 = v[col1]
            values2 = v[col2]
            x_axis = col1
            y_axis = col2

        else:
            values1 = v[col1]
            values2 = v[col2]
            x_axis = col1
            y_axis = col2

        if marker is None:
            marker = "o"

        fig, ax = plt.subplots()
        colors = [color_texture(texture) for texture in v["texture"]]
        sizes = [
            marker_size_from_high_card(flop, max_size=max_size)
            for flop in v["raw_flop"]
        ]
        ax.scatter(
            values1,
            values2,
            c=colors,
            label=v["raw_flop"],
            s=sizes,
            marker=marker,
            edgecolors="black",
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
        if legend:
            ax.legend(
                handles=legend_elements, loc="upper left", prop={"size": legend_size}
            )

        mplcursors.cursor(ax.collections, hover=True).connect(
            "add",
            lambda sel: sel.annotation.set_text(v["raw_flop"].iloc[sel.index]),
        )
        ax.set_xlabel(x_axis, fontsize=15)
        ax.set_ylabel(y_axis, fontsize=15)
        ax.set_title(
            f"{x_axis.capitalize()} vs {y_axis.capitalize()}".replace("_", " "),
            fontsize=20,
        )
        plt.show()
