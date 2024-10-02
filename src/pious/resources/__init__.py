from os import path as osp
import importlib.resources

_ALL_FLOPS = None
with open(osp.join(importlib.resources.files("pious.resources"), "all_flops.txt")) as f:
    _ALL_FLOPS = tuple(f.read().strip().split())


def get_all_flops():
    return _ALL_FLOPS
