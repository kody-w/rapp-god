"""@red/ember-empress — Ember Empress. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Ember Empress',
    "publisher": "red",
    "slug": 'ember-empress',
    "types": ['SOCIAL', 'WEALTH'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Ember Empress'
    types = ['SOCIAL', 'WEALTH']
    def imperial_rally(self):
        """Deal 80. All your SOCIAL allies +30 ATK."""
        return {"damage": 80, "cost": 2}
    def ember_decree(self):
        """Deal 125. Gain control of opponent's lowest-HP card until end of turn."""
        return {"damage": 125, "cost": 4}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
