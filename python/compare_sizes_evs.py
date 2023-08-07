from pyosolver import PYOSolver
from argparse import ArgumentParser
import os
from os import path as osp
from typing import Any, Dict, List
from pandas import DataFrame

PATH = r"C:\\PioSOLVER"
EXECUTABLE = r"PioSOLVER2-edge"


class SolveDB:
    """
    This represents a database of solves of different solves for a given tree configuration.
    """

    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        self.db_id = osp.basename(db_dir)
        self.cfrs = [
            osp.join(db_dir, f) for f in os.listdir(db_dir) if f.endswith(".cfr")
        ]
        self.flops = sorted([osp.basename(cfr).split(".")[0] for cfr in self.cfrs])
        self.flop_evs = {flop: None for flop in self.flops}
        self.flop_strats = {flop: None for flop in self.flops}
        self.flop_frequencies = {flop: None for flop in self.flops}

    def collect_evs(
        self, solver: PYOSolver, position: str = "OOP", node: str = "r:0", debug=False
    ):
        if debug:
            print(f"Collecting EVs for {self.db_id}")
            print("position: ", position)
            print(f"node: {node}")
        for flop in self.flops:
            cfr_path = osp.join(self.db_dir, flop + ".cfr")
            solver.load_tree(cfr_path)
            ev = solver.calc_ev(position, node)
            strat = solver.show_strategy(node)
            range_at_node = solver.show_range(position, node)
            children = solver.show_children(node)
            frequencies = {}
            total_freq = 0.0
            for child, s in zip(children, strat):
                # take dot product of range and s
                freq = sum([r * s for (r, s) in zip(range_at_node, s)])
                total_freq += freq
                frequencies[child["last_action"]] = freq

            # Now normalize
            for child in children:
                frequencies[child["last_action"]] /= total_freq

            self.flop_evs[flop] = ev
            self.flop_strats[flop] = strat
            self.flop_frequencies[flop] = frequencies
            if debug:
                print(f"{flop}")
                print(f"  EV: {ev}")
                action_freqs = "    ".join(
                    f"{action}: {freq:.2f}" for action, freq in frequencies.items()
                )
                print(f"  Action Frequencies: {action_freqs}")
                print(f"  Total Frequencies: {sum(frequencies.values())}")

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


def make_ev_table(dbs: List[SolveDB]) -> DataFrame:
    """
    make a table of EVs for each flop and each db_id and return it as a pandas
    DataFrame
    """
    all_flops = set()
    for db in dbs:
        all_flops.update(db.flops)
    all_flops = sorted(list(all_flops))

    # Now print a table of evs for each flop and each db_id
    header = ["Flop"] + [db.db_id for db in dbs]
    rows = []
    for flop in all_flops:
        row = [flop]
        for db in dbs:
            ev = db.flop_evs[flop]
            if ev is None:
                row.append("N/A")
            else:
                row.append(f"{ev:.2f}")
        rows.append(row)
    return DataFrame(rows, columns=header)


def main():
    args = parse_args()

    solver = PYOSolver(args.solver_path, args.solver_executable)
    dbs = [
        db for db in collect_cfrs(args.root_dir) if db.db_id not in args.excluded_db_ids
    ]

    for db in dbs:
        db.collect_evs(solver, debug=args.debug, position=args.position, node=args.node)

    if args.print_sizes_table:
        print(make_ev_table(dbs).to_string(index=False))


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "root_dir",
        type=str,
        help="Root directory of the solve DBs: should contain subdirectories, each of which contain cfr files",
    )
    parser.add_argument("--solver_path", type=str, default=PATH)
    parser.add_argument("--solver_executable", type=str, default=EXECUTABLE)
    parser.add_argument(
        "--choose_best_size",
        action="store_true",
        help="Print the best size for each flop",
    )
    parser.add_argument(
        "--print_sizes_table",
        action="store_true",
        help="Print a table of EVs of all solve databases found in root_dir",
    )
    parser.add_argument("--position", type=str, default="OOP")
    parser.add_argument("--node", type=str, default="r:0")
    parser.add_argument(
        "--excluded_db_ids", nargs="*", default=[], help="DB IDs (dir names) to exclude"
    )
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()
