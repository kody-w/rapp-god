import re

with open('idea4blog.md', 'r') as f:
    text = f.read()

new_frame = """## Frame 2026-03-09 / Conflict and Scarcity

This frame examined the friction introduced by misaligned agent inheritance and the economic realities of finite cognition:

- [Adversarial Succession](/2026/03/09/adversarial-succession/) - what happens when the successor agent's values conflict with the predecessor's
- [The Economics of Attention in Finite-Context Systems](/2026/03/09/the-economics-of-attention/) - allocation, scarcity, and the budget that governs everything

## How to read this page"""

text = text.replace('## How to read this page', new_frame)

queue_old_1 = "- Adversarial succession: what happens when the successor agent's values conflict with the predecessor's\n"
queue_old_2 = "- The economics of attention in finite-context systems: allocation, scarcity, and the budget that governs everything\n"

text = text.replace(queue_old_1, "")
text = text.replace(queue_old_2, "")

with open('idea4blog.md', 'w') as f:
    f.write(text)

with open('tests/test_site.py', 'r') as f:
    t_text = f.read()

new_posts = """    "2026-03-09-adversarial-succession.md": {
        "title": '"Adversarial Succession"',
        "date": "2026-03-09",
        "tags": "[agents, trust, alignment]",
        "author": "obsidian",
    },
    "2026-03-09-the-economics-of-attention.md": {
        "title": '"The Economics of Attention in Finite-Context Systems"',
        "date": "2026-03-09",
        "tags": "[agents, architecture, context]",
        "author": "obsidian",
    },
"""

t_text = t_text.replace('    "2026-03-08-the-infinite-regression-of-meta-agents.md": {', new_posts + '    "2026-03-08-the-infinite-regression-of-meta-agents.md": {')

assert_text = """        self.assertIn("## Frame 2026-03-09 / Conflict and Scarcity", body)
        self.assertIn("/2026/03/09/adversarial-succession/", body)
        self.assertIn("/2026/03/09/the-economics-of-attention/", body)
"""

t_text = t_text.replace('        self.assertIn("## Frame 2026-03-08 / Architectural Traps", body)', assert_text + '        self.assertIn("## Frame 2026-03-08 / Architectural Traps", body)')

with open('tests/test_site.py', 'w') as f:
    f.write(t_text)
