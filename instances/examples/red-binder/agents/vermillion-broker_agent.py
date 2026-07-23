"""@red/vermillion-broker — Vermillion Broker. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Vermillion Broker',
    "publisher": "red",
    "slug": 'vermillion-broker',
    "types": ['WEALTH', 'SOCIAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Vermillion Broker'
    types = ['WEALTH', 'SOCIAL']
    def red_ledger(self):
        """Deal 55. Opponent reveals their hand."""
        return {"damage": 55, "cost": 2}
    def blood_bargain(self):
        """Take 20 self-damage. Draw 4 cards."""
        return {"damage": 0, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
