"""@red/ochre-archivist — Ochre Archivist. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Ochre Archivist',
    "publisher": "red",
    "slug": 'ochre-archivist',
    "types": ['DATA', 'SOCIAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Ochre Archivist'
    types = ['DATA', 'SOCIAL']
    def recall(self):
        """Deal 30. Return any card from discard to hand."""
        return {"damage": 30, "cost": 1}
    def chronicle(self):
        """Deal 70. Opponent cannot use abilities next turn."""
        return {"damage": 70, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
