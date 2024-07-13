"""
Compare different combination reports. This effectively performs a join on two
aggregation reports.
"""

from aggregation.report import AggregationReport, Plotter
import pandas as pd
from typing import Optional, List, Tuple


class AggregationComparator:
    def __init__(
        self,
        report1: AggregationReport,
        report2: AggregationReport,
        lsuffix="_1",
        rsuffix="_2",
        join_type="left",
        compared_columns=None,
        join_on=None,
    ):
        """
        Create a comparison of two different aggregation reports. Under the
        hood this joins the reports on the "raw_flop" column, comparing evs.
        """
        # Defaults
        if compared_columns is None:
            compared_columns = ["ev", "eqr"]
        elif isinstance(compared_columns, str):
            compared_columns = [compared_columns]
        if join_on is None:
            join_on = ["raw_flop"]

        self.compared_columns = compared_columns
        self.join_on = join_on

        self.report1 = report1
        self.report2 = report2
        self.lsuffix = lsuffix
        self.rsuffix = rsuffix
        self.ip = report1.ip
        self.oop = report1.oop

        # We want to compute the join of these columns, this is a bit of logic
        # to do it
        all_actions = report1.get_actions() + report2.get_actions()
        remaining_cols = []
        to_exclude = join_on + compared_columns + all_actions
        for c in report1._df.columns:
            if c in to_exclude:
                continue
            remaining_cols.append(c)

        r1_projection = report1._df[join_on + compared_columns]
        r2_projection = report2._df[join_on + compared_columns]
        textures = report1._df[join_on + remaining_cols]
        df = pd.merge(
            r1_projection, r2_projection, on=join_on, suffixes=(lsuffix, rsuffix)
        )
        df = pd.merge(df, textures, on="raw_flop")
        self._df: pd.DataFrame = df
        self._view: pd.DataFrame = df.copy()
        self._current_filters = []
        self.hidden_columns = []
        self.texture_columns = []
        self.plotter = Plotter(self)
        self.set_default_hidden_columns()
        self.reset()

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
        self._current_filters = []
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
        ax_line=True,
    ):
        if filter is not None:
            self.filter(filter)

        if col1 is None and col2 is None:
            col1 = self.compared_columns[0] + self.lsuffix
            col2 = self.compared_columns[0] + self.rsuffix
        if col1 not in self._df or col2 not in self._df:
            raise ValueError(
                f"Could not find columns {col1} or {col2} in columns {self._df.columns}"
            )
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
            ax_line=ax_line,
        )

        if filter is not None:
            self.undo_filter()

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
