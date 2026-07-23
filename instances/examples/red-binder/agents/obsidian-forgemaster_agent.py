"""@red/obsidian-forgemaster — Obsidian Forgemaster. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Obsidian Forgemaster',
    "publisher": "red",
    "slug": 'obsidian-forgemaster',
    "types": ['CRAFT', 'LOGIC'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Obsidian Forgemaster'
    types = ['CRAFT', 'LOGIC']
    def black_glass_edge(self):
        """Deal 105. If target is CRAFT-typed, deal 50 more."""
        return {"damage": 105, "cost": 3}
    def remake(self):
        """Return any CRAFT card from discard to play with full HP."""
        return {"damage": 0, "cost": 4}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
