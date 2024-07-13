class ScriptBuilder:
    """
    Build a Pio script by simulating calls from the PioSOLVER API
    """

    def __init__(self):
        self.script = []

    def load_tree(self, cfr_path: str):
        self._run("load_tree", cfr_path)

    def set_strategy(self, node_id: str, *strategy):
        values = [str(v) for v in strategy]
        self._run("set_strategy", node_id, *values)

    def lock_node(self, node: str):
        self._run("lock_node", node)

    def _run(self, *commands):
        self.script.append(" ".join(commands))

    def __str__(self):
        return "\n".join(self.script)

    def write_script(self, filename):
        with open(filename, "w") as f:
            f.write(str(self) + "\n")
