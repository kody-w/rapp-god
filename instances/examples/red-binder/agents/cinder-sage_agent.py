"""@red/cinder-sage — Cinder Sage. RAPPcard agent (Red Binder)."""
__manifest__ = {
    "name": 'Cinder Sage',
    "publisher": "red",
    "slug": 'cinder-sage',
    "types": ['DATA', 'HEAL'],
    "spec_version": "rappcards/1.0",
}

class Agent:
    name = 'Cinder Sage'
    types = ['DATA', 'HEAL']
    def augur_the_ash(self):
        """Look at opponent's top 5 cards. Rearrange them."""
        return {"damage": 0, "cost": 2}
    def prophets_mending(self):
        """Deal 90. Heal all allies for 60."""
        return {"damage": 90, "cost": 4}
    def run(self, context):
        return {"agent": self.name, "types": self.types}
