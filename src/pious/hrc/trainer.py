import pious.hrc.hand as hrc_hand


class Game:
    def __init__(self, sim: hrc_hand.HRCSim):
        self.sim = sim
        self.stacks = [s for s in sim.settings.hand_data.stacks]
        self.blinds = sim.settings.hand_data.blinds
        self.initial_state = None


class HRCTrainer:
    def __init__(self, hand_path, node_id=0):
        self.solve = hrc_hand.Solve(hand_path)
        self.node_id = node_id
        self.node = self.solve.node_cache[node_id]
