from argparse import Namespace, _SubParsersAction
import sys
from ..pio import compute_single_card_blocker_effects, make_solver
from os import path as osp
from sys import exit
import typer
from typing_extensions import Annotated
from pathlib import Path


def blockers_cmd(
    solve_file: Annotated[Path, typer.Argument(help="Path to solve file")],
    node_id: Annotated[str, typer.Option(help="Node ID")] = None,
    num_hist_bins: Annotated[int, typer.Option(help="Number of histogram bins")] = 20,
    no_graph: Annotated[
        bool, typer.Option("--no-graph", help="Do not print graph")
    ] = False,
    no_graph_suits: Annotated[
        bool, typer.Option("--no-graph-suits", help="Do not print suits in graph")
    ] = False,
    per_card: Annotated[
        bool, typer.Option("--per-card", help="Print per card effects")
    ] = False,
    cards_to_print: Annotated[
        list[str], typer.Option(help="Cards to print effects for")
    ] = None,
    grid: Annotated[
        bool, typer.Option("--grid", help="Print grid of blocker effects")
    ] = False,
):
    """Compute single card blocker effects"""

    if node_id is None:
        node_id = "r:0"
    if not node_id.startswith("r:0"):
        node_id = "r:0" + node_id
    if not osp.exists(solve_file):
        print(f"No such file {solve_file}, exiting")
        exit(-1)
    solver = make_solver()
    solver.load_tree(str(solve_file))
    blocker_effects = compute_single_card_blocker_effects(
        solver, node_id, num_hist_bins
    )

    if not no_graph:
        blocker_effects.print_graph(print_suits=not no_graph_suits)
    if per_card or cards_to_print is not None:
        blocker_effects.print_per_card(cards_to_print=cards_to_print)
    if grid:
        blocker_effects.print_grid()
