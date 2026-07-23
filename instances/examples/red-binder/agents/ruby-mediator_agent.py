"""@red/ruby-mediator — Ruby Mediator. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Ruby Mediator',
    "publisher": "red",
    "slug": 'ruby-mediator',
    "types": ['SOCIAL', 'LOGIC'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Ruby Mediator'
    types = ['SOCIAL', 'LOGIC']
    def truce(self):
        """No damage is dealt next turn by either side."""
        return {"damage": 0, "cost": 2}
    def verdict(self):
        """Deal 75. Opponent discards 2 cards."""
        return {"damage": 75, "cost": 3}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
