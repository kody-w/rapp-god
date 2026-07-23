"""@red/ember-scout — Ember Scout. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Ember Scout',
    "publisher": "red",
    "slug": 'ember-scout',
    "types": ['CRAFT'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Ember Scout'
    types = ['CRAFT']
    def kindle(self):
        """Deal 20 damage. Draw a spark."""
        return {"damage": 20, "cost": 1}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
