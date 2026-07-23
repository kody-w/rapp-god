"""@red/kiln-priest — Kiln Priest. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Kiln Priest',
    "publisher": "red",
    "slug": 'kiln-priest',
    "types": ['HEAL', 'CRAFT'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Kiln Priest'
    types = ['HEAL', 'CRAFT']
    def consecrate(self):
        """Heal 50 HP. Until end of turn, allies take half damage from SHIELD."""
        return {"damage": 0, "cost": 2}
    def ash_blessing(self):
        """Deal 60. Restore an ally from the discard pile."""
        return {"damage": 60, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
