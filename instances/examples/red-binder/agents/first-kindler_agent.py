"""@red/first-kindler — The First Kindler. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'The First Kindler',
    "publisher": "red",
    "slug": 'first-kindler',
    "types": ['CRAFT', 'SOCIAL', 'HEAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'The First Kindler'
    types = ['CRAFT', 'SOCIAL', 'HEAL']
    def ignite_creation(self):
        """Deal 150. All your cards gain +40 HP for the game."""
        return {"damage": 150, "cost": 3}
    def eternal_flame(self):
        """Deal 240. If this card would be KO'd next turn, it survives with 1 HP instead."""
        return {"damage": 240, "cost": 5}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
