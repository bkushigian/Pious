"""
defines he 'Flops' class that allows convenient filtering of flops by board texture.
"""

import pandas as pd
from .resources import get_all_flops
from .util import card_tuple, ranks_rev, ahml


class Flops:
    def __init__(self):
        self._df = pd.DataFrame(data={"flop": get_all_flops()})
        self.hidden_columns = []
        self.set_default_hidden_columns()
        self._current_filters = []
        self._process_flops()
        self._compute_textures()
        self._view = self._df.copy()

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
            c1, c2, c3 = flop[:2], flop[2:4], flop[4:]
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

    def set_default_hidden_columns(self):
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
        self.hidden_columns = columns_to_suppress

    def __len__(self):
        return len(self._view)

    def __str__(self):
        view = self.view()
        flops = [flop for flop in self.view()["raw_flop"]]
        return "\n".join(flops)

    def __repr__(self):
        return f"<Flops: filters=\"{','.join(self._current_filters)}\" ({len(self)} flops)>"

    def dump(self) -> str:
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        s = str(self.view())
        pd.reset_option("display.max_rows")
        pd.reset_option("display.max_columns")
        pd.reset_option("display.width")
        return s
