"""@red/red-binder-prime — Red Binder, Prime. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Red Binder, Prime',
    "publisher": "red",
    "slug": 'red-binder-prime',
    "types": ['CRAFT', 'LOGIC', 'SOCIAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Red Binder, Prime'
    types = ['CRAFT', 'LOGIC', 'SOCIAL']
    def summon_the_collection(self):
        """Deal 120. Put 3 random Red Binder cards from deck into play."""
        return {"damage": 120, "cost": 3}
    def binders_judgment(self):
        """Deal 300. If opponent has any card with 'Red' in its name, deal 150 more."""
        return {"damage": 300, "cost": 5}
    def close_the_binder(self):
        """All cards in play return to their owners' decks. You win ties on 'first to draw'."""
        return {"damage": 0, "cost": 6}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
