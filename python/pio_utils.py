"""
A collection of PioSOLVER utility functions
"""

from typing import Dict, List, Tuple
from pyosolver import PYOSolver
from itertools import permutations

CARDS = tuple(f"{r}{s}" for r in "AKQJT98765432" for s in "shdc")
PATH = r"C:\\PioSOLVER"
EXECUTABLE = r"PioSOLVER2-edge"

FLOP = 1
TURN = 2
RIVER = 3


def get_all_lines(solver: PYOSolver) -> List[str]:
    """
    Given a node in the tree, return a list of all the lines in the tree.
    """
    lines = solver.show_all_lines
    effective_stacks = solver.show_effective_stacks()
    return [Line(line, effective_stacks=effective_stacks) for line in lines]


def money_in_per_street(streets_as_actions: List[List[str]]) -> List[int]:
    money_per_street = [0, 0, 0, 0]
    for street, actions in enumerate(streets_as_actions):
        for action in reversed(actions):
            if action.startswith("b"):
                money_per_street[street] = int(action[1:])
                break
    return money_per_street


def actions_to_streets(
    actions: List[str], starting_street=FLOP, effective_stacks=None
) -> Tuple[bool, List[List[str]]]:
    """
    Given a line in the gametree, break the line into a list
    of lines, one per street.

    :param line: A line in the gametree
    :returns: a list of actions broken up by street. The zeroth element is the
       root of the tree, which defaults to '' if no root is present

    # Example
    >>> actions_to_streets(["r","0","b125","b313","b501","c","c","c","c"])
    (False, [['r', '0'], ['b125', 'b313', 'b501', 'c'], ['c', 'c'], ['c']])
    >>> actions_to_streets(["b125","b313","b501","c","c","c","c"])
    (False, [[''], ['b125', 'b313', 'b501', 'c'], ['c', 'c'], ['c']])
    >>> actions_to_streets(["b125","b313","b501","c"])
    (False, [[''], ['b125', 'b313', 'b501', 'c'], []])
    >>> actions_to_streets(["r", "0", "b100", "b300", "c", "c", "b700", "c"], effective_stacks = 1000)
    (True, [['r', '0'], ['b100', 'b300', 'c'], ['c', 'b700', 'c']])

    """
    streets = []
    is_terminal = False
    if actions[0] == "r":
        streets.append(actions[:2])
        actions = actions[2:]
    else:
        streets.append([""])

    current_street = []
    for action in actions:
        current_street.append(action)
        if action.startswith("c") and len(current_street) > 1:
            streets.append(current_street)
            current_street = []

    if current_street:
        streets.append(current_street)

    else:
        all_in = (
            effective_stacks is not None
            and streets[-1][-1] == "c"
            and effective_stacks == sum(money_in_per_street(streets))
        )
        if not all_in and (
            len(streets) + starting_street < 5 and streets[-1][-1] != "f"
        ):
            # Should we add a final street empty street?
            #
            # This depends on whether there are any more player actions to come.
            # There are player actions when we have not reached the river, and when
            # the last action wasn't a fold.
            #
            # To tell if we add our starting street (1 for flop, 2 for turn, etc)
            # to the number of streets. `streets` has an entry for root, so
            # the maximal length of streets is 4.
            #
            # Consider if `streets = [['r', '0'], ['c', 'b120', 'c']]`. If this line starts on the
            #
            # then we need to add a street (FLOP + 2 = 3 < 4)
            streets.append([])
        else:
            is_terminal = True

    return is_terminal, streets


class Line:
    """
    A line in the gametree.

    A `Line` is created from a line string provided from PioSOLVER:
    >>> line = Line("r:0:c:b30:c:c")

    # Different Views of the Line

    The `Line` class offers several views of a line:

    * The raw string:

      >>> line.line_str
      'r:0:c:b30:c:c'

    * The line as a list of actions:

      >>> line.actions
      ['r', '0', 'c', 'b30', 'c', 'c']

    * The line as a list of streets of actions:

      >>> line.streets_as_actions
      [['r', '0'], ['c', 'b30', 'c'], ['c']]

    * The line as a list of streets of lines:

      >>> line.streets_as_lines
      ['r:0', 'c:b30:c', 'c']

    The street views (`Line.streets_as_lines` and `Line.streets_as_actions`) will
    possibly have empty streets when the line is not complete. For example, if
    the line is `r:0` then the associated street views will have an empty flop
    street.

    >>> root_line = Line("r:0")
    >>> root_line.streets_as_lines
    ['r:0', '']
    >>> root_line.streets_as_actions
    [['r', '0'], []]
    >>> call_cbet_line = Line("r:0:c:b30:c")
    >>> call_cbet_line.streets_as_lines
    ['r:0', 'c:b30:c', '']
    >>> call_cbet_line.streets_as_actions
    [['r', '0'], ['c', 'b30', 'c'], []]

    However, the `Line` class attempts to detect if a line is terminal
    (e.g., there are no more possible actions). This happens when:

    1. The line ends in a fold

        >>> Line("r:0:c:b30:f").streets_as_lines
        ['r:0', 'c:b30:f']
        >>> Line("r:0:c:b30:b100:f").streets_as_lines
        ['r:0', 'c:b30:b100:f']
        >>> Line("r:0:c:b30:b100:c:b250:f").streets_as_lines
        ['r:0', 'c:b30:b100:c', 'b250:f']

    2. All streets are complete (this depends on the starting street, e.g., 3
       complete streets for flop, 2 complete streets for turn, etc)

        >>> Line("r:0:c:b30:c:b75:c:b100:b300:c").streets_as_lines
        ['r:0', 'c:b30:c', 'b75:c', 'b100:b300:c']
        >>> Line("r:0:c:c:c:c", starting_street=TURN).streets_as_lines
        ['r:0', 'c:c', 'c:c']

    3. Players are all in. To determine this we need `effective_stacks` We cannot detect this condition without help, so
       we provide the optional argument `is_terminal` to the `Line` constructor.

       >>> Line("r:0:c:b30:b100:b900:c", effective_stacks=1000).streets_as_lines
       ['r:0', 'c:b30:b100:b900:c', '']
       >>> Line("r:0:c:b30:b100:b900:c:b100:c", effective_stacks=1000).streets_as_lines
       ['r:0', 'c:b30:b100:b900:c', 'b100:c']
       >>> Line("r:0:c:b30:b100:b900:c:b100:c", effective_stacks=2000).streets_as_lines
       ['r:0', 'c:b30:b100:b900:c', 'b100:c', '']

    This class only checks the first two conditions. The third condition depends
    on data that isn't available here, so we cannot account for it.


    # Expanding a Line into nodes

    In addition to offering several views of a line, the `Line` class
    facilitates the expansion of a line into concrete nodes by interspersing
    the line with all possible combinations of cards.

    For example, if the line is: `r:0:c:b30:c:c:b100:c:c` and the possible
    cards are `['As', 'Ks', 'Qs']`, then the nodes would be:

    >>> available_cards = ['As', 'Ks', 'Qs']
    >>> dead_cards = [card for card in CARDS if card not in available_cards]
    >>> line.get_node_ids(dead_cards=dead_cards)
    ['r:0:c:b30:c:As:c', 'r:0:c:b30:c:Ks:c', 'r:0:c:b30:c:Qs:c']
    >>> Line("r:0:c:c").get_node_ids(dead_cards=dead_cards)
    ['r:0:c:c:As', 'r:0:c:c:Ks', 'r:0:c:c:Qs']

    """

    def __init__(self, line: str, starting_street=FLOP, effective_stacks=None):
        self.line_str = line
        self._starting_street = starting_street
        self._is_terminal = None
        self._effective_stacks = effective_stacks
        self._money_in_per_street = [0, 0, 0, 0]
        self.actions: List[str] = []
        self.streets_as_actions: List[List[str]] = []
        self.streets_as_lines: List[str] = []
        self.nodes: Dict[Tuple[str], List[List[str]]] = {}
        self._setup(line)

    def _setup(self, line):
        """
        Set up different views of this line by breaking it into actions and
        grouping the actions by streets.
        """
        self.actions = line.split(":")
        self.is_terminal, self.streets_as_actions = actions_to_streets(
            self.actions,
            starting_street=self._starting_street,
            effective_stacks=self._effective_stacks,
        )
        self.streets_as_lines = [":".join(street) for street in self.streets_as_actions]

        # Update money in per street
        for street, actions in enumerate(self.streets_as_actions):
            # find last bet action
            for action in reversed(actions):
                if action[0] == "b":
                    self._money_in_per_street[street] = int(action[1:])
                    break

    def _check_is_well_formed(self) -> bool:
        """
        Check if this line is well formed.

        TODO: Implement this
        """
        return True

    def get_node_ids(self, dead_cards=None):
        """
        Get the nodes associated with this line. If the nodes have not been
        computed, compute and cache them.
        """

        if dead_cards is None:
            dead_cards = []
        # Make dead cards hashable
        dead_cards = tuple(sorted(dead_cards))
        if dead_cards not in self.nodes:
            nodes = self.streets_to_nodes(dead_cards=dead_cards)
            self.nodes[dead_cards] = nodes
        return self.nodes[dead_cards]

    def streets_to_nodes(self, isomorphism: bool = False, dead_cards=None) -> List[str]:
        """
        Translate a list of streets representing a line to a list of nodes

        :param streets: The streets of a line to translate
        :param dead_cards: A list of cards that are not in the deck anymore (e.g., on the board)
        :param isomorphism: Whether to use suit isomorphism or not (not implemented)
        :returns: A list of all possible nodes that can be made from the line
        :raises NotImplementedError: If isomorphism is True
        :raises ValueError: If the line would contain more than 2 cards

        >>> line = Line("r:0:c:b30:c:c")
        >>> available_cards = ['As', 'Ks', 'Qs']
        >>> dead_cards = [card for card in CARDS if card not in available_cards]
        >>> line.streets_to_nodes(dead_cards=dead_cards)
        ['r:0:c:b30:c:As:c', 'r:0:c:b30:c:Ks:c', 'r:0:c:b30:c:Qs:c']
        >>> line = Line("r:0:c:b30:c:c:b100:c:c")
        >>> line.streets_to_nodes(dead_cards=dead_cards)
        ['r:0:c:b30:c:As:c:b100:c:Ks:c', 'r:0:c:b30:c:As:c:b100:c:Qs:c', 'r:0:c:b30:c:Ks:c:b100:c:As:c', 'r:0:c:b30:c:Ks:c:b100:c:Qs:c', 'r:0:c:b30:c:Qs:c:b100:c:As:c', 'r:0:c:b30:c:Qs:c:b100:c:Ks:c']
        """
        streets = self.streets_as_lines
        if len(streets) > 4:
            raise ValueError(f"Cannot expand line with more than 3 streets: {streets}")

        if isomorphism:
            raise NotImplementedError("Suit isomorphism not implemented yet")
        available_cards = [c for c in CARDS if c not in dead_cards]
        root = streets[0]
        templated = ":{}:".join(streets[1:])
        templated_line = f"{root}:{templated}".strip(":")
        num_cards = len(streets) - 2

        nodes = []
        if num_cards > 2:
            raise ValueError(f"Cannot expand line with more than 2 cards: {streets}")
        for cards in permutations(available_cards, num_cards):
            nodes.append(templated_line.format(*cards))

        return nodes

    def n_streets(self) -> int:
        """
        Return the number of streets in this line, not including the root
        """
        return len(self.streets_as_lines) - 1

    def is_oop(self):
        """
        Return True if the player acting is out of position

        >>> Line("r:0").is_oop()
        True
        >>> Line("r:0:c").is_oop()
        False
        >>> Line("r:0:c:b30").is_oop()
        True
        >>> Line("r:0:c:b30:c").is_oop()
        True
        >>> Line("r:0:c:b30:c:c").is_oop()
        False
        """
        last_street = self.streets_as_actions[-1]
        return len(last_street) % 2 == 0

    def is_ip(self):
        """
        Return True if the player acting is in position
        """
        return not self.is_oop()

    def current_street(self) -> int:
        """
        Return True if the current street is the given street

        :param street: The street to check
        :returns: True if the current street is the given street
        """

        return self._starting_street + self.n_streets() - 1

    def is_flop(self):
        """
        Return True if the current street is the flop

        >>> Line("r:0").is_flop()
        True
        >>> Line("r:0:c").is_flop()
        True
        >>> Line("r:0:c:b30").is_flop()
        True
        >>> Line("r:0:c:b30:c").is_flop()
        False
        """
        return self.current_street() == FLOP

    def is_turn(self):
        """
        Return True if the current street is the turn

        >>> Line("r:0").is_turn()
        False
        >>> Line("r:0:c:c").is_turn()
        True
        >>> Line("r:0:c:b30:c").is_turn()
        True
        >>> Line("r:0:c:b30:c:c").is_turn()
        True
        >>> Line("r:0:c:b30:c:c:c").is_turn()
        False
        """
        return self.current_street() == TURN

    def is_river(self):
        """
        Return True if the current street is the river

        >>> Line("r:0").is_river()
        False
        >>> Line("r:0:c:c:c:c").is_river()
        True
        >>> Line("r:0:c:b1000:c", effective_stacks=1000).is_river()
        False
        """
        return self.current_street() == RIVER

    def is_facing_bet(self):
        """
        Return True if the player is facing a bet

        >>> Line("r:0").is_facing_bet()
        False
        >>> Line("r:0:c").is_facing_bet()
        False
        >>> Line("r:0:c:b30").is_facing_bet()
        True
        >>> Line("r:0:c:b30:c").is_facing_bet()
        False
        >>> Line("r:0:c:b30:f").is_facing_bet()
        False
        """
        return self.actions[-1].startswith("b")

    def __str__(self):
        return self.line_str

    def __repr__(self):
        return f"Line({self.line_str})"


def make_solver(
    install_path=PATH,
    executable=EXECUTABLE,
    debug=False,
    log_file=None,
    store_script=False,
) -> PYOSolver:
    """
    Create a new solver instance.

    :param install_path: The path to the PioSOLVER installation
    :param executable: The name of the executable
    :param debug: Whether to run in debug mode (prints to stdout)
    :param log_file: Store all solver communications to a log file (this can get big!)
    :param store_script: Store all solver commands to a script file `script.txt`
    :returns: A new solver instance
    """
    return PYOSolver(
        install_path,
        executable,
        debug=debug,
        log_file=log_file,
        store_script=store_script,
    )


def is_flop(line: Line) -> bool:
    return line.is_flop()


def is_turn(line: Line) -> bool:
    return line.is_turn()


def is_river(line: Line) -> bool:
    return line.is_river()


def is_facing_bet(line: Line) -> bool:
    return line.is_facing_bet()


def is_ip(line: Line) -> bool:
    return line.is_ip()


def is_oop(line: Line) -> bool:
    return line.is_oop()


def is_facing_bet(line: Line) -> bool:
    return line.is_facing_bet()


def filter_lines(lines: List[Line], filters=None):
    if filters is None:
        return lines

    def filt(line):
        return all((f(line) for f in filters))

    return [line for line in lines if filt(line)]


def get_all_n_street_lines(lines: List[Line], n: int) -> List[Line]:
    return [line for line in lines if line.n_streets() == n]


def get_flop_lines(lines: List[Line]) -> List[Line]:
    return [line for line in lines if line.is_flop()]


def get_turn_lines(lines: List[Line]) -> List[Line]:
    return [line for line in lines if line.is_turn()]


def get_river_lines(lines: List[Line]) -> List[Line]:
    return [line for line in lines if line.is_river()]
