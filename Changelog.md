# Changelog

## v0.0.0.dev17
- Various fixes to hand categorizations
- Fixes/improvements/new tests

## v0.0.0.dev16
- Fixed pio2 vs pio3 bug for `show_boards_no_iso`

## v0.0.0.dev15

## v0.0.0.dev14
- Check if out exists before aggregation during `pious aggregate`
- Added `pious` script on `pip install` (no longer need to run `python -m pious ...`)

## v0.0.0.dev13
- added executables, including
  - aggregate
- added aggregation support (initial)
- added hand classification (simple)

## v0.0.0.dev12
- added `pious.flops` and the `Flops` class to easily filter flops
- Fixed bug in `pious.pio.solver.Node.__repr__()`

## v0.0.0.dev11
- fixed bug in blocker module (incorrect board was being passed to the equity calculator)
- improved blocker example (histograms, per combo blocked equity listing, colors)
- updated required python from 3.8 -> 3.11 (for `tomlib` module)`
- updated required `ansi` from 3 to 3.7
- Added `find_isomorphic_board` to `pious.pio.database`
- Updated `color_suit`
- Skipping PioSOLVER tests (tests that require PioSOLVER) on non-Windows platforms

## v0.0.0.dev10

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