"""@red/ironveil-alchemist — Ironveil Alchemist. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Ironveil Alchemist',
    "publisher": "red",
    "slug": 'ironveil-alchemist',
    "types": ['CRAFT', 'LOGIC'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Ironveil Alchemist'
    types = ['CRAFT', 'LOGIC']
    def crucible_splash(self):
        """Deal 50 damage. Target becomes CRAFT-typed next turn."""
        return {"damage": 50, "cost": 2}
    def transmute(self):
        """Deal 90. Discard a card; draw two."""
        return {"damage": 90, "cost": 4}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
