"""
Handle pio ranges
"""

from typing import Dict, List


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
