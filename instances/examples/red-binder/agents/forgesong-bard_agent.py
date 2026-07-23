"""@red/forgesong-bard — Forgesong Bard. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Forgesong Bard',
    "publisher": "red",
    "slug": 'forgesong-bard',
    "types": ['SOCIAL', 'CRAFT'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Forgesong Bard'
    types = ['SOCIAL', 'CRAFT']
    def anthem_of_the_red(self):
        """Deal 45 damage. If singing, +20."""
        return {"damage": 45, "cost": 2}
    def verse_of_mending(self):
        """Heal 60 HP to any one ally."""
        return {"damage": 0, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
