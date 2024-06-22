# Pious: The Pio Utility Suite

Various Pio Utilities

**Warning:** _This library is still under construction. All interfaces, classes, files, etc **will** be changed. I'm open sourcing this for feedback/collaboration_

## Installing Requirements

You'll need to install Python3.x (not sure the minimal x version, but anything
>= 3.9 should be good). You also need to install some requirements with `pip
install -r requirements.txt`.

## Aggregation Reports

To use the `AggregationReport`, start a `python` session from the `python`
directory, and import the aggregation report module. Then create a new
`AggregationReport` by passing in the path to the folder containing the
`AggregationReport` (and optionally including the path to the solve database
that you used to generate the aggregation report):

```python
import aggregation.report as ar

# With just the report
r = ar.AggregationReport(PATH_TO_REPORT_FOLDER)
# With report and solve database
r = ar.AggregationReport(PATH_TO_REPORT_FOLDER, PATH_TO_SOLVE_DB)
```

You can run `r.plot()` to get a nice visualization, `r.filter()` to focus only
on boards you're interested in, and `r.reset()` to start over again.