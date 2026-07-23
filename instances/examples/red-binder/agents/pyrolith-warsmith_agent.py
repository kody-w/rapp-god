"""@red/pyrolith-warsmith — Pyrolith Warsmith. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Pyrolith Warsmith',
    "publisher": "red",
    "slug": 'pyrolith-warsmith',
    "types": ['CRAFT', 'SHIELD'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Pyrolith Warsmith'
    types = ['CRAFT', 'SHIELD']
    def hammerfall(self):
        """Deal 95. Opponent is Stunned (skips attack)."""
        return {"damage": 95, "cost": 2}
    def forge_the_field(self):
        """Deal 130. Draw until you have 5 cards."""
        return {"damage": 130, "cost": 4}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
