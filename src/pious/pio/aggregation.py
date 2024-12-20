from typing import Dict, Optional, Tuple, List
import pandas as pd
import os
from os import path as osp
from io import StringIO
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplcursors
import webbrowser
import tempfile
import pydoc
from pathlib import Path

from ..util import ranks_rev, ahml
from .util import *
from .database import (
    CFRDatabase,
    apply_permutation,
    ALL_SUIT_PERMUTATIONS,
    board_to_ranks_suits,
)

plt.ion()


def load_report_to_df(report_csv_path: str) -> Tuple[List[str], str, pd.DataFrame]:
    """
    Read in a report a return a (header, body, dataframe) tuple
    """
    with open(report_csv_path) as f:
        lines = f.readlines()
    header = lines[:3]
    body = StringIO("\n".join(lines[3:]))
    df = pd.read_csv(body)
    df = df.drop(df.index[-1])
    return header, body, df


class AggregationReport:
    def __init__(
        self,
        agg_report_directory: str,
        cfr_database: Optional[str | CFRDatabase] = None,
        report_cache: Optional[str] = None,
        spot_name: Optional[str] = None,
    ):
        """Create a new `AggregationReport`

        Args:
            agg_report_directory (str): the location of the directory
            containing the aggregation report

            db_loc (Optional[str], optional): _description_. Defaults to None.
            the location of the database of solves that were used to generate
            the aggregation report
        """
        self._ensure_is_valid_agg_report_directory(agg_report_directory)
        self.type = "RAW_REPORT"
        self.agg_report_directory = agg_report_directory
        self.report_csv_path = osp.join(agg_report_directory, "report.csv")
        self.report_info_path = osp.join(agg_report_directory, "info.txt")
        self.hands_ev_path = osp.join(agg_report_directory, "handsEV.csv")
        self.spot_name = spot_name
        self._report_cache: Dict[str, AggregationReport] = (
            {} if report_cache is None else report_cache
        )
        if self.agg_report_directory in self._report_cache:
            raise ValueError(
                f"There is already a cached AggregationReport associated with {self.agg_report_directory}"
            )
        self._report_cache[self.agg_report_directory] = self
        self.ip = False
        self.oop = False
        self.info = None
        self.plotter = Plotter(self)
        self._df = None
        self._view: pd.DataFrame = None
        self._current_filters = []
        self.hidden_columns = []
        self.texture_columns = []
        self.cfr_database = None
        if cfr_database is not None:
            if isinstance(cfr_database, str):
                self.cfr_database = CFRDatabase(cfr_database)
            elif isinstance(cfr_database, CFRDatabase):
                self.cfr_database = cfr_database
            else:
                raise ValueError(
                    f"Illegal cfr_database value {cfr_database}: must either be a CFRDatabase or a string representing the path to a solve database"
                )
        self._load_info()
        self._load_report()
        self.set_default_hidden_columns()

        # We keep track of the current _view_ of the aggregation report, which
        # allows us to make modifications (e.g., through filters, sorting, etc)
        # without modifying the original
        self.reset()

    def set_db_loc(self, db_loc):
        self.cfr_database = CFRDatabase(db_loc)

    def _load_report(self):
        """
        Load the dataframe from the raw csv passed in.
        """
        self.header, self.body, self._df = load_report_to_df(self.report_csv_path)
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

    def reset(self, filter=None):
        """
        Reset the view, optionally with a new filter
        """
        self._view = self._df.copy()
        self._current_filters = []
        if filter:
            self.filter(filter)
        return self

    def filters(self, join: Optional[str | bool] = None, parens=True):
        if join is not None and join is not False:
            fs = self._current_filters
            if parens:
                fs = [f"({f})" for f in fs]
            if join == True:
                join = " and "
            return join.join(fs)

        return self._current_filters.copy()

    def joined_filters(self):
        return "(" + ") and (".join(self._current_filters) + ")"

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

    def describe(self, cols=None):
        v = self.view()
        if cols is not None:
            v = v[cols]
        return v.describe()

    def plot(
        self,
        col1=None,
        col2=None,
        title=None,
        min_size=None,
        max_size=None,
        labels=None,
        marker=None,
        sort_single_column=None,
        legend=None,
        legend_size=None,
        plot_size_inches=None,
        filter=None,
        xlim=None,
        ylim=None,
    ):
        if filter is not None:
            self.filter(filter)
        self.plotter.scatter(
            col1=col1,
            col2=col2,
            title=title,
            min_size=min_size,
            max_size=max_size,
            labels=labels,
            marker=marker,
            sort_single_column=sort_single_column,
            legend=legend,
            legend_size=legend_size,
            plot_size_inches=plot_size_inches,
            xlim=xlim,
            ylim=ylim,
        )

        if filter is not None:
            self.undo_filter()

    def open_board_in_pio(self, board, node=None):
        if node is None:
            node = self.info.node_id
        self.cfr_database.open_board_in_pio(board, node=node)

    def parent(self):
        ard = self.agg_report_directory
        if osp.basename(ard) == "Root":
            return None
        par_dir = str(Path(ard).parent.absolute())
        try:
            self._ensure_is_valid_agg_report_directory(par_dir)
        except RuntimeError as e:
            print(e)
            return None
        # Is valid parent dir
        if par_dir not in self._report_cache:
            return AggregationReport(
                par_dir, self.cfr_database, report_cache=self._report_cache
            )
        return self._report_cache[par_dir]

    def take_action(self, action_directory: str):
        ard = self.agg_report_directory
        d = osp.join(ard, action_directory)
        dirs = [
            d
            for d in os.listdir(self.agg_report_directory)
            if osp.isdir(osp.join(ard, d))
        ]
        # Normalize the action directory
        na = action_directory.upper().replace("_", "").replace(" ", "")
        # Look for an exact match
        matching_dir = None
        for d in dirs:
            nd = d.upper().replace("_", "").replace(" ", "")
            if nd == na:
                if matching_dir is not None:
                    raise ValueError(
                        f"Ambiguous match: {d} and {matching_dir} both normalize to {nd}"
                    )
                matching_dir = d
        if matching_dir is None:  # No exact match, so lets find a unique prefix
            matching_dir = None  # Redundant, but to be clear :)
            for d in dirs:
                nd = d.upper().replace("_", "").replace(" ", "")
                if nd.startswith(na):
                    if matching_dir is not None:
                        raise ValueError(
                            f"Ambiguous fuzzy match: {na} is a prefix to both {d} and {matching_dir}: cannot resolve which action to take"
                        )
                    matching_dir = d
        if matching_dir is None:
            raise ValueError(
                f"Unable to find an diretory in {dirs} corresponding to action {action_directory}"
            )
        new_ard = osp.join(ard, matching_dir)

        if new_ard not in self._report_cache:
            return AggregationReport(
                agg_report_directory=new_ard,
                cfr_database=self.cfr_database,
                report_cache=self._report_cache,
            )
        return self._report_cache[new_ard]

    def ion(self):
        plt.ion()

    def ioff(self):
        plt.ioff()

    def _ensure_is_valid_agg_report_directory(self, d):
        for file in ["report.csv", "info.txt", "handsEV.csv"]:
            if not osp.isfile(osp.join(d, file)):
                raise RuntimeError(f"Cannot find {file} in report directory {d}")

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
        with open(self.report_info_path) as f:
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

    def __getitem__(self, item):
        ranks, suits = board_to_ranks_suits(item)
        v = self.view()
        for permutation in ALL_SUIT_PERMUTATIONS:
            new_suits = apply_permutation(suits, permutation)
            cards = [f"{r}{s}" for (r, s) in zip(ranks, new_suits)]
            board = " ".join(cards)
            result = v.loc[v["raw_flop"] == board]
            if len(result) > 0:
                return result
        return None

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

    def get_action_dirs(self):
        ard = self.agg_report_directory
        return [
            d
            for d in os.listdir(self.agg_report_directory)
            if osp.isdir(osp.join(ard, d))
        ]

    def __str__(self):
        view = self.view()
        view_str = str(view)
        s = f"""AggregationReport for {self.info.player} at {self.info.line} [ {self.agg_report_directory} ]

{view_str}"""

        return s

    def __len__(self):
        return len(self._view)

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
        self.data_point_labels = True
        self.marker = "o"
        self.legend = True
        self.legend_size = 12
        self.sort_single_column = False
        self.plot_size_inches = (18.5, 10.8)
        self.data_point_labels = None

    def scatter(
        self,
        col1=None,
        col2=None,
        title=None,
        labels=None,
        min_size=None,
        max_size=None,
        marker=None,
        sort_single_column=None,
        legend=None,
        legend_size=None,
        plot_size_inches=None,
        ax_line=None,
        xlim=None,
        ylim=None,
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
        labels = labels or self.data_point_labels
        min_size = min_size or self.min_size
        max_size = max_size or self.max_size
        marker = marker or self.marker
        if legend is None:
            legend = self.legend
        if legend_size is None:
            legend_size = self.legend_size
        if sort_single_column is None:
            sort_single_column = self.sort_single_column
        plot_size_inches = plot_size_inches or self.plot_size_inches

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

        if ax_line is None:
            ax_line = False

        fig, ax = plt.subplots()
        fig.set_size_inches(*plot_size_inches)
        colors = [color_texture(texture) for texture in v["texture"]]
        sizes = [
            marker_size_from_high_card(flop, max_size=max_size)
            for flop in v["raw_flop"]
        ]
        scatter = ax.scatter(
            values1,
            values2,
            c=colors,
            label=v["raw_flop"],
            s=sizes,
            marker=marker,
            edgecolors="black",
        )
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)

        if ax_line:

            pt = max(min(ax.get_xlim()), min(ax.get_ylim()))
            ax.axline((pt, pt), slope=1)

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

        self.data_point_labels = tuple(v["raw_flop"])
        mplcursors.cursor(ax.collections, hover=True).connect(
            "add",
            lambda sel: sel.annotation.set_text(v["raw_flop"].iloc[sel.index]),
        )
        ax.set_xlabel(x_axis, fontsize=15)
        ax.set_ylabel(y_axis, fontsize=15)
        if title is None:
            title = f"{x_axis.capitalize()} vs {y_axis.capitalize()}".replace("_", " ")
            title += f"\n{self.report.filters(join=True, parens=False)}"
        ax.set_title(
            title,
            fontsize=20,
        )
        fig.canvas.callbacks.connect("pick_event", self._make_on_pick_callback())
        scatter.set_picker(True)
        plt.show()

    def _make_on_pick_callback(self):
        labels = self.data_point_labels

        def on_click(event: PickEvent):
            ind = list(event.ind)
            mouseevent = event.mouseevent
            if mouseevent.button == 1 and mouseevent.dblclick:
                if len(ind) > 0:
                    i = ind[0]
                    print(labels[i])
                    board = labels[i]
                    print(f"Opening {board} in PioViewer")
                    self.report.open_board_in_pio(board)

        return on_click
