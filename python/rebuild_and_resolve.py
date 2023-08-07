"""This script is used to rebuild and resolve forgotten streets in a solve."""

from pyosolver import PYOSolver
from sys import argv

PATH = r"C:\\PioSOLVER"
EXECUTABLE = r"PioSOLVER2-edge"


def helper():
    tree = r"C:\PioSOLVER\Saves\6max\3BP\30-Flop-Subset\BN-v-SB\b50\6s5h3s.cfr"
    solver = PYOSolver(path=PATH, executable_name=EXECUTABLE)
    solver.load_tree(tree)
    solver.rebuild_forgotten_streets()
    node_ids = get_all_river_root_node_ids(solver)
    return solver, tree, node_ids


def add_chance_action_template_to_line(line):
    """_summary_

    r:0:b125:b313:b501:c:c:c:c
         ^

    r:0:b125:b313:b501:c:{}:c:c:{}:c

    Args:
        line (_type_): _description_
    """
    l = line[2:]
    i = 0
    # First Street
    while i < len(l) - 1:
        if l[i].startswith("b") and l[i + 1].startswith("c"):
            # Call node
            l.insert(i + 2, "{}")
            i += 3
        elif l[i].startswith("c") and l[i + 1].startswith("c"):
            # Check check node
            l.insert(i + 2, "{}")
            i += 3
        else:
            i += 1
    return l


def find_last_index(l, elem):
    for i in range(len(l) - 1, -1, -1):
        if l[i] == elem:
            return i
    raise ValueError("Element not found in list")


def transform_all_lines(all_lines):
    all_nodes = set()
    for line in all_lines:
        l = add_chance_action_template_to_line(line.split(":"))
        if "{}" in l:
            idx = find_last_index(l, "{}")
            all_nodes.add(tuple(l[: idx + 1]))
        else:
            continue
    return all_nodes


def get_all_river_root_node_ids(solver: PYOSolver):
    node_info = solver.show_node("r")
    board = node_info["board"]
    all_lines = solver.show_all_lines()
    all_lines = transform_all_lines(all_lines)
    all_river_lines = {line for line in all_lines if line.count("{}") == 2}
    all_river_nodes = []
    for c1 in all_cards:
        if c1 in board:
            continue
        for c2 in all_cards:
            if c2 in board or c2 == c1:
                continue

            for river_line in all_river_lines:
                rl = ":".join(river_line)
                all_river_nodes.append(rl.format(c1, c2))
    return sorted(list(all_river_nodes))


all_cards = [
    "As",
    "Ks",
    "Qs",
    "Js",
    "Ts",
    "9s",
    "8s",
    "7s",
    "6s",
    "5s",
    "4s",
    "3s",
    "2s",
    "Ah",
    "Kh",
    "Qh",
    "Jh",
    "Th",
    "9h",
    "8h",
    "7h",
    "6h",
    "5h",
    "4h",
    "3h",
    "2h",
    "Ad",
    "Kd",
    "Qd",
    "Jd",
    "Td",
    "9d",
    "8d",
    "7d",
    "6d",
    "5d",
    "4d",
    "3d",
    "2d",
    "Ac",
    "Kc",
    "Qc",
    "Jc",
    "Tc",
    "9c",
    "8c",
    "7c",
    "6c",
    "5c",
    "4c",
    "3c",
    "2c",
]


def get_river_lines(all_lines):
    lines = [line.split(":") for line in all_lines]


def load_and_rebuild(tree_path):
    solver = PYOSolver(path=PATH, executable_name=EXECUTABLE)
    solver.load_tree(tree_path)
    solver.rebuild_forgotten_streets()
    return solver


def main():
    tree_path = argv[1]
    solver = PYOSolver(path=PATH, executable_name=EXECUTABLE)
    solver.load_tree(tree_path)
    print("Rebuilding forgotten streets...")
    solver.rebuild_forgotten_streets()
    print("Rebuild Done!")
    print("Getting all lines")
    all_lines = solver.show_all_lines()
    print("All lines:")
    print(all_lines)


if __name__ == "__main__":
    main()
