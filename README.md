# Pious: The Pio Utility Suite

Pious provide a Python wrapper for a PioSOLVER instance and provides
convenience functions and abstractions to make working with PioSOLVER
easier.

**Warning:** _This library is still under construction. All interfaces, classes, files, etc. **will** be changed. I'm open sourcing this for feedback/collaboration._

## Install

Install with `pip install pious`. Requires Python 3.11 or later.

## Solver Interface

Pious provides `pious.pio.solver.Solver` to wrap a PioSOLVER instance. This can
be constructed directly, but we recommend using `pious.pio.util.make_solver()`:

```python
# examples/load_tree.py
from pious.pio.util import make_solver
from pious.pio.resources import get_test_tree

solver = make_solver()
solver.load_tree(get_test_tree())  # Replace with your tree
solver.load_all_nodes()  # Required for partial saves in Pio3
tree_info = solver.show_tree_info()
print(f"Board: {tree_info['Board']}")
print(f"Pot: {tree_info['Pot']}")
print(f"EffectiveStacks: {tree_info['EffectiveStacks']}")

lines = solver.show_all_lines()
print("Last 10 lines:", lines[-10:])
```

## Configuration

By default `make_solver` will try to invoke `C:\PioSOLVER\PioSOLVER3-edge.exe`.
You can configure default behavior by placing a `pious.toml` in your home
directory. Here is a sample `pious.toml`:

```toml
[pio]
install_directory="C:\\PioSOLVER"
pio_version_no="2"
pio_version_type="pro"
```

## Lines

PioSOLVER deals in _lines_ (e.g., `show_all_lines`), such as
`r:0:c:c:b300:b850:c`. Pious provides a high-level wrapper, `Line`, around
low-level Pio lines that gives many quality-of-life improvements. See
`examples\line_example.py` for details:

```python
from pious.pio.line import Line

# ...
line = Line("r:0:c:b12:c:c:b77:b221:c:c")
print("Line:", line)
print("  IP?                 ", line.is_ip())
print("  Current Street?     ", line.current_street())
print("  Actions:            ", line.actions)
print("  Streets as Actions: ", line.streets_as_actions)
print("  Streets as Lines:   ", line.streets_as_lines)
print("  Facing Bet?         ", line.is_facing_bet())
```

## Aggregation Reports

To use the `AggregationReport`, start a `python` session from the `python`
directory, and import the aggregation report module. Then create a new
`AggregationReport` by passing in the path to the folder containing the
`AggregationReport` (and optionally including the path to the solve database
that you used to generate the aggregation report).
See `examples\aggregation_example.py` for more info:

```python
# Excerpt from examples\aggregation_example.py

from pious.pio.aggregation import AggregationReport
import pious.pio.resources as resources

report = AggregationReport(get_aggregation_root(), get_database_root())
print(report)
print(report.describe())

report.ioff()  # turn off matplotlib's interactive mode
report.plot()  # exit report to continue

report.filter("r1 == 14") # filter for ace high boards
report.plot()

report.reset()
report.filter("r1 < 14 and flushdraw") # non ace high AND flushdraw boards
report.plot()
```

You can run `r.plot()` to get a nice visualization, `r.filter()` to focus only
on boards you're interested in, and `r.reset()` to start over again.