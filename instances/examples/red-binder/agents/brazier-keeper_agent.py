"""@red/brazier-keeper — Brazier Keeper. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Brazier Keeper',
    "publisher": "red",
    "slug": 'brazier-keeper',
    "types": ['SHIELD', 'CRAFT'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Brazier Keeper'
    types = ['SHIELD', 'CRAFT']
    def flame_bulwark(self):
        """Until next turn, this card takes 50 less damage. Counter with 30 fire damage."""
        return {"damage": 0, "cost": 2}
    def burning_stance(self):
        """Deal 65. Self gains 'Burning' — +20 ATK but -10 HP/turn."""
        return {"damage": 65, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
