from pyosolver import PYOSolver
from typing import List, Optional


class AggregateReportColumns:
    def __init__(
        self,
        global_frequencies: bool = True,
        hand_weight: bool = True,
        matchups: bool = True,
        ev: bool = True,
        eq: bool = True,
        eqr: bool = True,
        action_frequencies: bool = True,
    ):
        self.global_frequencies = global_frequencies
        self.hand_weight = hand_weight
        self.matchups = matchups
        self.ev = ev
        self.eq = eq
        self.eqr = eqr
        self.action_frequencies = action_frequencies


class PIOAggregateReport:
    def __init__(
        self,
        cfr_files: List[str],
        agg_report_columns: Optional[None],
        solver: PYOSolver,
        nodes=None,
    ):
        self.cfr_files = tuple(cfr_files)
        self.solver = solver
        self.agg_report_columns = agg_report_columns or AggregateReportColumns()
        self.nodes = nodes or ["r:0"]
        self.reports = {}

    def run(self):
        for node in self.nodes:
            self.reports[node] = self._run_node(node)
