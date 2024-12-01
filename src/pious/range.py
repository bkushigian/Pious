"""
Handle pio ranges
"""

from typing import Dict, List
import numpy as np
from .util import (
    CARDS,
    NUM_COMBOS,
    PIO_HAND_ORDER,
    combo_as_full_combos,
    get_pio_combo_index,
    is_full_combo,
    is_preflop_combo,
)


class Range:
    range_array: np.ndarray

    def __init__(self, rng):
        if isinstance(rng, Range):
            self.range_array = np.copy(rng.range_array)
        elif isinstance(rng, (np.ndarray, np.generic)):
            if len(rng) != NUM_COMBOS:
                raise ValueError(
                    f"Illegal range array: must be length {NUM_COMBOS} but has length {len(rng)}"
                )
            self.range_array = np.copy(rng)
        elif isinstance(rng, list):
            if len(rng) != NUM_COMBOS:
                raise ValueError(
                    f"Illegal range list: must be length {NUM_COMBOS} but has length {len(rng)}"
                )
            self.range_array = np.array(rng)
        elif isinstance(rng, str):
            self.range_array = np.zeros(shape=NUM_COMBOS, dtype=np.float64)
            self._initialize_from_str(rng)
        else:
            raise RuntimeError("Could not compute range")

        if self.range_array is None:
            raise ValueError(
                f"Input range must be a length {NUM_COMBOS} np.array or list, or must be a valid range string"
            )

    def _initialize_from_str(self, range_str):
        if ": " in range_str or " :" in range_str:
            raise ValueError(
                "No spaces allowed next to a colon; that is, nothing of the form 'AA: 0.5'"
            )
        range_str = range_str.strip()
        items = range_str.split()
        items = [s.split(",") for s in items]
        flattened = [x.strip() for xs in items for x in xs if x]

        for entry in flattened:
            # Each entry is either of the form "combo:freq" or "combo".
            # Map "combo:freq" to "combo:1.0", and expand each combo to full combos.
            # So "ATs" becomes (AhTh, AsTs, AdTd, AcTc), 1.0, and
            # "AhTd:0.3" becomes (AhTd,), 0.3
            k, v = entry, 1.0
            if ":" in entry:
                k, v = entry.split(":")
                v = float(v)
            if v < 0.0:
                v = 0.0
            elif v > 1.0:
                v = 1.0
            full_combos = combo_as_full_combos(k)
            for full_combo in full_combos:
                self.range_array[get_pio_combo_index(full_combo)] = v

    def __getitem__(self, x):
        if isinstance(x, int):
            if x < 0 or x >= NUM_COMBOS:
                raise ValueError(f"Index {x} not in range [{0}, {NUM_COMBOS})")
            return self.range_array[x]
        if isinstance(x, str):
            if is_full_combo(x):
                return self.range_array[get_pio_combo_index(x)]
            if is_preflop_combo(x):
                full_combos = combo_as_full_combos(x)
                indices = [get_pio_combo_index(c) for c in full_combos]
                values = [self.range_array[i] for i in indices]
                return sum(values) / len(values)

    def __setitem__(self, x, v):
        v = float(v)
        if v > 1.0:
            v = 1.0
        if v < 0.0:
            v = 0.0
        if isinstance(x, int):
            if x < 0 or x >= NUM_COMBOS:
                raise ValueError(f"Index {x} not in range [{0}, {NUM_COMBOS})")
            self.range_array[x] = v
        elif isinstance(x, str):
            for fc in combo_as_full_combos(x):
                self.range_array[get_pio_combo_index(fc)] = v

    def __sub__(self, c: str):
        """
        Remove a card from this range and
        """

        if c not in CARDS:
            raise ValueError(f"Invalid card: {c}")

        combos_to_exclude = [combo for combo in PIO_HAND_ORDER if c in combo]
        r = Range(self)
        for combo in combos_to_exclude:
            r[combo] = 0.0
        return r

    def num_combos(self):
        return sum(self.range_array)

    def pio_str(self):
        """
        Return this range as a string to be passed to Pio
        """
        return " ".join([str(x) for x in self.range_array])


class PreflopRange:
    def __init__(self, preflop_range=None):
        self.raw_range = preflop_range
        self.preflop_range = {}
        if isinstance(preflop_range, str):
            self.preflop_range = self._parse_range_string(preflop_range)
        elif isinstance(preflop_range, dict):
            self.preflop_range.update(preflop_range)
        elif preflop_range is None:
            pass
        else:
            raise ValueError(f"Unknown range format: {preflop_range}")

    def _parse_range_string(self, preflop_range_str: str) -> Dict[str, float]:
        preflop_range_list = [e for e in preflop_range_str.split(",") if e]
        return self._parse_range_list(preflop_range_list)

    def _parse_range_list(self, preflop_range_list: List[str]) -> Dict[str, float]:
        d = {}
        for e in preflop_range_list:
            hand = e
            freq = 1.0
            if ":" in e:
                hand, freq = e.split(":")
            freq = float(freq)
            d[hand] = freq
        return d

    def __getitem__(self, item):
        return self.preflop_range.get(item, default=0.0)

    def __str__(self):
        xs = [f"{k}:{v}" for (k, v) in self.preflop_range.items()]
        return ",".join(xs)

    def __repr__(self):
        return f"PreflopRange({str(self)})"


def preflop_range(preflop_range: str) -> PreflopRange:
    return PreflopRange(preflop_range)
