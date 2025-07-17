"""
Equity Graph Module

This module draws an equity graph to stdout and quits.
"""

from ansi.colour.rgb import rgb256
from ansi.colour.fx import reset, bold, crossed_out
from ansi.colour import fg
from ..pio import Solver, Node
import math

HORIZONTAL = "─"
VERTICAL = "│"
TOP_LEFT = "┌"
TOP_RIGHT = "┐"
BOTTOM_LEFT = "└"
BOTTOM_RIGHT = "┘"

TOP_LEFT_ROUND = "╭"
TOP_RIGHT_ROUND = "╮"
BOTTOM_LEFT_ROUND = "╰"
BOTTOM_RIGHT_ROUND = "╯"

LEFT_T = "├"
RIGHT_T = "┤"
TOP_T = "┬"
BOTTOM_T = "┴"
CROSS = "┼"


def compute_equity_graph_indices(
    equity_matchup_tuples: list[(float, float)],
    height: int,
    width: int,
    min_equity: float = 0.0,
    max_equity: float = 1.0,
) -> tuple[list[tuple[int, int]], dict[tuple[int, int], int]]:
    """
    Computes the indices for each equity entry in the graph.
    """

    # sort by equity
    equity_matchup_tuples = [(i, e, w) for i, (e, w) in
                             enumerate(equity_matchup_tuples) if not math.isnan(e) and not math.isnan(w)]
    equity_matchup_tuples.sort(key=lambda x: x[1])

    if min_equity is None:
        min_equity = min(equity for equity, _ in equity_matchup_tuples)
    if max_equity is None:
        max_equity = max(equity for equity, _ in equity_matchup_tuples)

    if min_equity < 0:
        min_equity = 0.0
    if max_equity > 1:
        max_equity = 1.0

    if min_equity >= max_equity:
        raise ValueError("min_equity must be less than max_equity")

    sum_weights = sum(weight for _, _, weight in equity_matchup_tuples)

    if sum_weights == 0:
        raise ValueError("Sum of weights cannot be zero")

    total_weight = 0.0

    graph_indices = {}  # Map (x, y) to indices
    result = []

    for idx, equity, weight in equity_matchup_tuples:
        if weight < 0:
            raise ValueError(f"Invalid weight {weight}: values must be in [0, ...)")
        if equity < min_equity or equity > max_equity:
            raise ValueError(
                f"Invalid equity {equity}: values must be in [{min_equity}, {max_equity}]"
            )
        # x is horizontal position, corresponding to weight
        # y is vertical position, corresponding to equity
        x = int(width * total_weight / sum_weights)
        y = height - int(equity / (max_equity - min_equity) * height)

        total_weight += weight
        result.append((x, y))
        graph_indices[(x, y)] = idx

    return result, graph_indices


def draw_borders(graph: list[list[str]], width: int, height: int, borders=True) -> None:
    if borders:
        # Draw the border
        for x in range(width):
            graph[0][x] = HORIZONTAL
            graph[height - 1][x] = HORIZONTAL
        for y in range(height):
            graph[y][0] = VERTICAL
            graph[y][width - 1] = VERTICAL
        graph[0][0] = TOP_LEFT
        graph[0][width - 1] = TOP_RIGHT
        graph[height - 1][0] = BOTTOM_LEFT
        graph[height - 1][width - 1] = BOTTOM_RIGHT


def draw_equity_graph(
    equities: list[(float, float)],
    height: int = 27,
    width: int = 80,
    colors: list = None,
    response_to_action: list = None,
    borders: bool = True,
) -> None:
    """
    Draws an equity graph to stdout.

    Args:
        equities (list[(float, float)]): List of tuples representing player's
        (weight, equity) pairs.
    """
    graph_width = width - 2 if borders else width
    graph_height = height - 2 if borders else height
    positions, graph_indices = compute_equity_graph_indices(
        equities, graph_height, graph_width, 0.0, 1.0
    )
    graph = [[" " for _ in range(width)] for _ in range(height)]
    draw_borders(graph, width, height, borders)

    if colors:
        for (x, y), idx in graph_indices.items():
            color = colors[idx] or fg.green
            graph[y + 1][x + 1] = color("*")
    else:
        for (x, y), idx in graph_indices.items():
            graph[y + 1][x + 1] = fg.green("*")
        # Print the graph
    for row in graph:
        print("".join(row))


def draw_equity_graph_for_player(
    solver: Solver,
    node: str | Node,
    height: int = 27,
    width: int = 80,
    action_to_inspect: str | None = None,
) -> None:
    """
    Draws an equity graph for a specific player.

    Args:
        solver (Solver): The solver instance containing the game state.
        height (int): Height of the graph.
        width (int): Width of the graph.
    """
    node = solver.show_node(node)
    hero_position = node.get_position()
    villain_position = "IP" if hero_position == "OOP" else "OOP"
    equities, matchups, _ = solver.calc_eq_node(position=villain_position, node_id=node)
    values = [
        (e, m)
        for e, m in zip(equities, matchups)
    ]
    if action_to_inspect is not None:
        children_actions = solver.show_children_actions(node)
        if action_to_inspect not in children_actions:
            raise ValueError(
                f"Action '{action_to_inspect}' not found in children actions: {children_actions}"
            )
        response_freqs, response_actions, response_evs = analyze_response_node(
            solver, node, action_to_inspect
        )
        # For now, only handle when fold is an action
        if "f" not in response_actions:
            pass
        else:
            pass
        response_node_id = solver.show_node(node).node_id + ":" + action_to_inspect
        response_node = solver.show_node(response_node_id)
        position = response_node.get_position()
        evs = solver.calc_ev(position=position, node=response_node_id)[0]
        colors = compute_colors(
            response_freqs, response_actions, response_evs, evs, position
        )
        draw_equity_graph(values, height, width, colors=colors)
    else:
        draw_equity_graph(values, height, width)


def compute_colors(response_freqs, response_actions, response_evs, evs, position):
    """
    Computes colors for the equity graph based on response frequencies and EVs.

    For now, only compute based on frequencies.
    """
    colors = []
    if "f" in response_actions:
        fold_index = response_actions.index("f")
        # Three colors: pure fold (blue), pure non-call (green), and mixed
        # (yellow
        for freqs in response_freqs:
            if freqs[fold_index] > 0.95:
                colors.append(fg.blue)
            elif freqs[fold_index] < 0.5:
                colors.append(fg.green)
            else:
                colors.append(fg.yellow)
        return colors
    else:
        return [fg.green for _ in range(len(evs))]

def analyze_response_node(solver: Solver, parent_node: str, action_to_inspect: str):
    node = solver.show_node(parent_node)
    node_id = node.node_id
    response_node_id = f"{node_id}:{action_to_inspect}"

    response_node_strat = solver.show_strategy(response_node_id)
    response_actions = solver.show_children_actions(response_node_id)
    if len(response_actions) != len(response_node_strat):
        raise ValueError(
            f"Response node {response_node_id} has {len(response_actions)} actions "
            f"but {len(response_node_strat)} strategies."
        )
    # zip the strat into tuples of action frequencies
    response_freqs_by_hand = list(zip(*response_node_strat))
    response_evs_by_hand = []
    response_node = solver.show_node(response_node_id)
    if response_node is None:
        raise ValueError(f"Cannot analyze action that leads to chance or terminal node: {response_node_id}")
    position = response_node.get_position()
    response_evs = []
    for a in response_actions:
        n = f"{response_node_id}:{a}"
        evs, matchups = solver.calc_ev(position=position, node=n)
        response_evs.append(evs)

    return response_freqs_by_hand, response_actions, response_evs
