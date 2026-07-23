"""@red/hearthwarden-pup — Hearthwarden Pup. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Hearthwarden Pup',
    "publisher": "red",
    "slug": 'hearthwarden-pup',
    "types": ['HEAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Hearthwarden Pup'
    types = ['HEAL']
    def warm_embers(self):
        """Heal 30 HP to self or ally."""
        return {"damage": 0, "cost": 1}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
