# Changelog

## v0.0.0.dev10
- fixed bug in blocker module (incorrect board was being passed to the equity calculator)
- improved blocker example (histograms, per combo blocked equity listing, colors)
- updated required python from 3.8 -> 3.11 (for tomlib module)
- updated requried ansi from 3 to 3.7
- Added `find_isomorphic_board` to `pious.pio.database`
- Updated `color_suit`

## v0.0.0.dev9
- sanitized some solver.Solver inputs
- added blocker effects module
- added type hints to solver.Solver
- made solver.Solver play nicer with pious types (e.g., Range, Node)
- improved import structures
- can now import all major/important interfaces directly from `pious.pio`:
  ```python
  from pious.pio import (
    Solver,
    make_solver,
    rebuild_and_resolve,
    compute_equities,
    compute_single_card_blocker_effects
  )
  ```

  previously this was done by importing directly from modules (which is still possible):

  ```python
  from pious.pio.solver import Solver
  from pious.pio.util import make_solver
  from pious.pio.rebuild_utils import rebuild_and_resolve
  from pious.pio.equity import compute_equities
  from pious.pio.blockers import compute_single_card_blocker_effects
  ```

  - increased testing
  - fixed some PioSolver 2.0 -> 3.0 changes (namely, added calls to `load_all_nodes`)


## v0.0.0.dev8
- added homepage to pyproject.toml
- created hrc package