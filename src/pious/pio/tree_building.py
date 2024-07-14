"""
Responsible for reading and writing tree building scripts found in C:\\PioSOLVER\\TreeBuilding
"""

from typing import List
from os import path as osp
from pious.pio.range import PreflopRange


def try_value_as_int(maybe_int):
    """
    Try to convert a value to an int and return if successful, otherwise
    return the original value.
    """
    try:
        return int(maybe_int)
    except ValueError:
        return maybe_int


def try_value_as_literal(data_string: str):
    """
    Try to convert a value to a common type (bool, int, float) and return if
    successful, otherwise return the original value.
    """
    s = data_string.upper()
    if s == "TRUE":
        return True
    elif s == "FALSE":
        return False
    try:
        return int(data_string)
    except ValueError:
        pass
    try:
        return float(data_string)
    except ValueError:
        pass
    return data_string


def split_sizing_list(sizings: str):
    values = sizings.split(",")
    values = [try_value_as_literal(s) for v in values for s in v.split(" ") if s]
    return values


def parse_postflop_tree_build_config(config_path: str):
    if not osp.exists(config_path):
        raise ValueError("No such config as", config_path)
    with open(config_path) as f:
        lines = f.readlines()
    print("Read lines from disk")
    kwargs = {}
    upi_commands = []
    print("Parsing lines")
    for line in lines:
        l = line.strip()
        if "#" in l:
            l = l.strip("#")
            k, v = l.split("#")
            kwargs[k] = v
        elif l:
            upi_commands.append(l)
    print("done reading lines")
    return PostflopTreeBuildingConfig(upi_commands=upi_commands, **kwargs)


class StreetConfig:
    """
    Configure a street of betting
    """

    def __init__(self, ip=False):
        self.ip = ip
        self.bet_size = []
        self.raise_size = []
        self.donk_bet_size = []
        self.add_allin = False

    def __getitem__(self, key):
        if key == "BetSize":
            return self.bet_size
        if key == "RaiseSize":
            return self.raise_size
        elif key == "DonkBetSize":
            return self.donk_bet_size
        elif key == "AddAllin":
            return self.add_allin

    def __setitem__(self, key, value):
        if key == "BetSize":
            self.bet_size = split_sizing_list(value)
        if key == "RaiseSize":
            self.raise_size = split_sizing_list(value)
        elif key == "DonkBetSize":
            self.donk_bet_size = split_sizing_list(value)
        elif key == "AddAllin":
            self.add_allin = value == True

    def __str__(self):
        items = [
            f"BetSize:{self.bet_size}",
            f"RaiseSize:{self.raise_size}",
            f"DonkBetSize:{self.donk_bet_size}",
            f"AddAllin:{self.add_allin}",
        ]
        return ", ".join(items)


class PostflopTreeBuildingConfig:
    """
    A Postflop Tree Building Configuration
    """

    def __init__(self, upi_commands=None, **kwargs):
        self.type = "NoLimit"
        self.range_oop: PreflopRange = PreflopRange()
        self.range_ip: PreflopRange = PreflopRange()
        self.board = None
        self.pot = None
        self.effective_stacks = None
        self.allin_threshold = None
        self.add_allin_only_if_less_than_this_times_the_pot = 0
        self.flop_config_oop = StreetConfig(ip=False)
        self.turn_config_oop = StreetConfig(ip=False)
        self.river_config_oop = StreetConfig(ip=False)
        self.flop_config_ip = StreetConfig(ip=True)
        self.turn_config_ip = StreetConfig(ip=True)
        self.river_config_ip = StreetConfig(ip=True)

        self.added_lines = []
        self.removed_lines = []
        self.upi_commands = []

        self._dict = {
            "Type": self.type,
            "Range0": self.range_oop,
            "Range1": self.range_ip,
            "Board": self.board,
            "Pot": self.pot,
            "EffectiveStacks": self.effective_stacks,
            "AllinThreshold": self.allin_threshold,
            "AddAllinOnlyIfLessThanThisTimesThePot": self.add_allin_only_if_less_than_this_times_the_pot,
            "FlopConfig": self.flop_config_oop,
            "TurnConfig": self.turn_config_oop,
            "RiverConfig": self.river_config_oop,
            "FlopConfigIP": self.flop_config_ip,
            "TurnConfigIP": self.turn_config_ip,
            "RiverConfigIP": self.river_config_ip,
        }

        self._parse_kwargs(**kwargs)
        self._parse_upi_commands(upi_commands)

    def _parse_kwargs(self, **kwargs):
        """
        Parse the key/value pairs defined in
        """
        for k, v in kwargs.items():
            self[k] = v

    def _parse_upi_commands(self, upi_commands: List[str]):
        for c in upi_commands:
            pass
            c = c.strip()
            if c.startswith("add_line"):
                self.added_lines.append(c)
            elif c.startswith("remove_line"):
                self.removed_lines.append(c)
            else:
                self.upi_commands.append(c)

    def validate(self):
        """
        Ensure that the necessary portions of the tree building configuration
        have been set.
        """
        if self.board is None:
            raise RuntimeError("PostflopTreeBuildingConfig.board is not set")
        if self.pot is None:
            raise RuntimeError("PostflopTreeBuildingConfig.pot is not set")
        if self.effective_stacks is None:
            raise RuntimeError("PostflopTreeBuildingConfig.effective_stacks is not set")
        if self.allin_threshold is None:
            raise RuntimeError("PostflopTreeBuildingConfig.allin_threshold is not set")

    def __getitem__(self, key):
        if key in self._dict:
            return self._dict[key]
        else:
            raise ValueError(f"Unknown key: {key}")

    def __setitem__(self, key, value):
        if "." in key:
            xs = key.split(".")
            key, keys = xs[0], xs[1:]
            keys = ".".join(keys)
            self[key][keys] = value
            return
        if key not in self._dict:
            raise ValueError(f"Unknown key: {key}")
        self._dict[key] = value
        # This is gross, but we need to track the update in class state as well
        if key == "Type":
            self.type = value
        elif key == "Range0":
            self.range_oop = value
        elif key == "Range1":
            self.range_ip = value
        elif key == "Board":
            self.board = value
        elif key == "Pot":
            self.pot = value
        elif key == "EffectiveStacks":
            self.effective_stacks = value
        elif key == "AllinThreshold":
            self.allin_threshold = value
        elif key == "AddAllinOnlyIfLessThanThisTimesThePot":
            self.add_allin_only_if_less_than_this_times_the_pot = value
        elif key == "FlopConfig":
            self.flop_config_oop = value
        elif key == "TurnConfig":
            self.turn_config_oop = value
        elif key == "RiverConfig":
            self.river_config_oop = value
        elif key == "FlopConfigIP":
            self.flop_config_ip = value
        elif key == "TurnConfigIP":
            self.turn_config_ip = value
        elif key == "RiverConfigIP":
            self.river_config_ip = value

    def __str__(self):
        items = []
        for k, v in self._dict.items():
            items.append(f"{str(k)}:{str(v)}")
        return "\n".join(items)
