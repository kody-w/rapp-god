"""@red/crimson-herald — Crimson Herald. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Crimson Herald',
    "publisher": "red",
    "slug": 'crimson-herald',
    "types": ['SOCIAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Crimson Herald'
    types = ['SOCIAL']
    def rally_cry(self):
        """Deal 15 damage. All allies +10 ATK next turn."""
        return {"damage": 15, "cost": 1}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
