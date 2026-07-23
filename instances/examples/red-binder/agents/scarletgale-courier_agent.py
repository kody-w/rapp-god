"""@red/scarletgale-courier — Scarletgale Courier. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Scarletgale Courier',
    "publisher": "red",
    "slug": 'scarletgale-courier',
    "types": ['SOCIAL', 'CRAFT'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Scarletgale Courier'
    types = ['SOCIAL', 'CRAFT']
    def rush_the_red_road(self):
        """Deal 65. Attack again this turn."""
        return {"damage": 65, "cost": 1}
    def invoke_the_wind(self):
        """Deal 100. Draw until you have 6 cards."""
        return {"damage": 100, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
