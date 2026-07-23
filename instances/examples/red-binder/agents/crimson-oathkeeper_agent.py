"""@red/crimson-oathkeeper — Crimson Oathkeeper. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Crimson Oathkeeper',
    "publisher": "red",
    "slug": 'crimson-oathkeeper',
    "types": ['SHIELD', 'HEAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Crimson Oathkeeper'
    types = ['SHIELD', 'HEAL']
    def oath_of_iron(self):
        """All allies take 50% damage while this card stands. Heal 40."""
        return {"damage": 0, "cost": 3}
    def keepers_reprisal(self):
        """Deal 110. +40 more if an ally was KO'd this game."""
        return {"damage": 110, "cost": 4}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
