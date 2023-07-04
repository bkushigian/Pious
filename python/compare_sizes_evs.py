from pyosolver import PYOSolver
from argparse import ArgumentParser
import os
from os import path as osp
from typing import Dict, List

PATH = r"C:\\PioSOLVER"
EXECUTABLE = r"PioSOLVER2-edge"


class SolveDB:
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        self.db_id = osp.basename(db_dir)
        self.cfrs = [
            osp.join(db_dir, f) for f in os.listdir(db_dir) if f.endswith(".cfr")
        ]
        self.flops = sorted([osp.basename(cfr).split(".")[0] for cfr in self.cfrs])
        self.flop_evs = {flop: None for flop in self.flops}

    def collect_evs(
        self, solver: PYOSolver, position: str = "OOP", node: str = "r", debug=False
    ):
        if debug:
            print(f"Collecting EVs for {self.db_id}")
        for flop in self.flops:
            cfr_path = osp.join(self.db_dir, flop + ".cfr")
            solver.load_tree(cfr_path)
            ev = solver.calc_ev(position, node)
            if debug:
                print(f"  EV on {flop}: {ev}")
            self.flop_evs[flop] = ev

    def __repr__(self):
        return f"SolveDB(db_id:{self.db_id}, #flops:{len(self.flops)})"


def collect_cfrs(root_dir: str) -> List[SolveDB]:
    dbs = []
    for dir in os.listdir(root_dir):
        print(dir)
        dir_path = osp.join(root_dir, dir)
        if osp.isdir(dir_path):
            dbs.append(SolveDB(dir_path))
    return dbs


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "root_dir",
        type=str,
        help="Root directory of the solve DBs: should contain subdirectories, each of which contain cfr files",
    )
    parser.add_argument("--solver_path", type=str, default=PATH)
    parser.add_argument("--solver_executable", type=str, default=EXECUTABLE)

    args = parser.parse_args()
    solver = PYOSolver(args.solver_path, args.solver_executable)

    root_dir = args.root_dir
    dbs = collect_cfrs(root_dir)

    for db in dbs:
        db.collect_evs(solver, debug=True)

    all_flops = set()
    for db in dbs:
        all_flops.update(db.flops)
    all_flops = sorted(list(all_flops))

    # Now print a table of evs for each flop and each db_id
    header = ["Flop"] + [db.db_id for db in dbs]
    print(",".join(header))
    for flop in all_flops:
        row = [flop]
        for db in dbs:
            ev = db.flop_evs[flop]
            if ev is None:
                row.append("N/A")
            else:
                row.append(f"{ev:.2f}")
        print(",".join(row))


main()
