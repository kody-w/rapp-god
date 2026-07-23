# Drop in an agent

The simplest unit in RAPP is a single Python file with a class that
inherits from `BasicAgent`. Drop the file into your agents directory; the
brainstem auto-discovers it on the next request.

## Get an agent

Browse the registry: https://kody-w.github.io/RAR/

Each card is a single `*_agent.py` file. Download or copy the source.

## Install

```bash
cp my_agent.py ~/.brainstem/agents/
```

That's it. The brainstem hot-loads anything in that folder.

## Test it

```bash
curl -X POST http://localhost:7071/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "use the my_agent agent", "user_guid": "test"}'
```

## Anatomy

```python
from agents.basic_agent import BasicAgent

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyAgent'
        self.metadata = {
            "name": self.name,
            "description": "What this agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "..."}
                },
                "required": ["query"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, query: str):
        return f"You asked: {query}"
```

## Reference

- Registry: https://github.com/kody-w/RAR
- Registry spec: [../SPEC/registry/SPEC.md](../SPEC/registry/SPEC.md)
- Kernel spec: [../SPEC/kernel/SPEC.md](../SPEC/kernel/SPEC.md)
