"""@red/scarlet-courier — Scarlet Courier. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Scarlet Courier',
    "publisher": "red",
    "slug": 'scarlet-courier',
    "types": ['SOCIAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Scarlet Courier'
    types = ['SOCIAL']
    def breakneck_dash(self):
        """Deal 40. This card can attack again next turn for free."""
        return {"damage": 40, "cost": 1}
    def sealed_dispatch(self):
        """Search deck for any card. Add to hand."""
        return {"damage": 0, "cost": 2}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
