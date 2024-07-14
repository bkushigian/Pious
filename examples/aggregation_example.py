from pious.pio.aggregation import AggregationReport
import pious.pio.resources as resources
from ansi.color import fg
from ansi.colour.fx import italic

report = AggregationReport(
    resources.get_aggregation_root(), resources.get_database_root()
)

# Reports are printable
print(report)

# And can be described
print(report.describe())

# We can plot reports. Use report.ioff if this is in a script (not in an
# interactive environment like the REPL).
report.ioff()

print()
print(italic(fg.green("Pro Tip: try double-clicking the dots!")))
print(fg.cyan("Plot 1/3: All Boards (exit plot to continue)"))
report.plot()


# We can filter reports to get more detailed information.
# For instance, ace high boards:
print(fg.cyan("Plot 2/3: Ace High Boards (exit plot to continue)"))
report.filter("r1 == 14")
report.plot(title="Ace High Boards", legend=False)


# Or non-ace high boards that are flush draws
print(fg.cyan("Plot 3/3: Non Ace High Boards w/ Flush Draws (exit plot to continue)"))
report.reset(filter="r1 < 14 and flushdraw")
report.plot(title="Non Ace High Boards w/ Flush Draws", legend=False)
