"""@red/scorchmark-duelist — Scorchmark Duelist. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Scorchmark Duelist',
    "publisher": "red",
    "slug": 'scorchmark-duelist',
    "types": ['CRAFT', 'SOCIAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Scorchmark Duelist'
    types = ['CRAFT', 'SOCIAL']
    def first_blood(self):
        """Deal 70. Doubles if opponent is full HP."""
        return {"damage": 70, "cost": 1}
    def signature_strike(self):
        """Deal 140. If this KOs, draw 3 cards."""
        return {"damage": 140, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
