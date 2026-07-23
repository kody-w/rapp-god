"""@red/blood-accord — The Blood Accord. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'The Blood Accord',
    "publisher": "red",
    "slug": 'blood-accord',
    "types": ['SOCIAL', 'SHIELD', 'DATA'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'The Blood Accord'
    types = ['SOCIAL', 'SHIELD', 'DATA']
    def seal_the_pact(self):
        """All your cards gain Resistance to the opponent's highest-DMG type."""
        return {"damage": 0, "cost": 4}
    def invoke_the_accord(self):
        """Deal 200. Heal every one of your cards to full."""
        return {"damage": 200, "cost": 5}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
