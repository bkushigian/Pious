from os import path as osp

import importlib.resources
from pious.hrc.hand import HRCSim


def get_test_hrc_sim(sim="2.5_rfi"):
    sims_path = importlib.resources.files("pious.hrc.resources.sims")
    sim_root = osp.join(sims_path, sim)
    return HRCSim(sim_root)
