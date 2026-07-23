# Quest 02 — First Agent

**Goal:** teach the brainstem a new skill by dropping in one Python file.
No restart, no framework, no build step.

## 1. Write it

Save this as `~/.brainstem/src/rapp_brainstem/agents/dice_agent.py`:

```python
import random
from openrappter.agents.basic_agent import BasicAgent

class DiceAgent(BasicAgent):
    def __init__(self):
        self.name = 'Dice'
        self.metadata = {
            "name": self.name,
            "description": "Rolls dice. Use when the user asks to roll, flip, or pick randomly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sides": {"type": "integer", "description": "Number of sides (default 6)."}
                },
                "required": []
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        sides = int(kwargs.get('sides') or 6)
        return f"🎲 rolled a {random.randint(1, sides)} (d{sides})"
```

(Or drag the file onto the web UI — same thing.)

## 2. Use it

Agents reload from disk **on every request** — just ask: *"roll a d20"*.
The response will show `AGENT CALLED DICE` with the result.

## 3. What you learned

- `agents/*_agent.py` + a class extending `BasicAgent` = auto-discovered skill
- `metadata.description` is how the LLM decides when to call it
- `perform(**kwargs)` returns a string; the LLM weaves it into the reply

Next: [give it memory](03-memory.md). When an agent is worth keeping, publish
it to [RAR](https://github.com/kody-w/RAR) — disk is temporary, the registry
is forever.
