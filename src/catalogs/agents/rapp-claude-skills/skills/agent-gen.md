# Agent Generation Skill

Generate production-ready agent code from descriptions.

## Trigger
`/agent-gen`

## Description
Create Python agent code compatible with CommunityRAPP's Azure Function architecture.

## Actions

### create
Generate a new agent.

**Parameters:**
- `name` - Agent name (PascalCase)
- `description` - What the agent does
- `parameters` - JSON schema for agent inputs
- `capabilities` - List of capabilities (web, storage, api, etc.)

**Example:**
```
/agent-gen create
  --name "WeatherAgent"
  --description "Fetches weather for a location"
  --parameters '{"location": {"type": "string", "required": true}}'
  --capabilities "web,api"
```

### from-template
Use a predefined template.

**Parameters:**
- `template` - basic, memory, multi-step, orchestrator
- `name` - Agent name
- `customize` - Customization instructions

### validate
Check agent code for RAPP compatibility.

**Parameters:**
- `file` - Path to agent file

### test
Generate test cases for an agent.

**Parameters:**
- `agent` - Agent name or file path

## Agent Template

```python
from agents.basic_agent import BasicAgent

class {AgentName}Agent(BasicAgent):
    def __init__(self):
        self.name = '{AgentName}'
        self.metadata = {
            "name": self.name,
            "description": "{description}",
            "parameters": {
                "type": "object",
                "properties": {
                    # Generated from parameters
                },
                "required": []
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        # Agent logic here
        return "Result"
```

## Capabilities

| Capability | Imports Added |
|------------|--------------|
| web | requests, httpx |
| storage | AzureFileStorageManager |
| api | Azure OpenAI client |
| memory | ContextMemoryAgent patterns |
| multi | Multi-agent orchestration |

## Output

Generated agents include:
- `{name}_agent.py` - Main agent code
- `{name}_demo.json` - Demo/test data
- `{name}_test.py` - Unit tests
- `agent_tester.html` - Browser-based tester

## Deployment Path

```
/agent-gen create → agents/{name}_agent.py
                  → Upload to Azure File Storage
                  → Available in CommunityRAPP
                  → Published to RAR (https://github.com/kody-w/RAR)
                  → Announced on rapp-commons via a signed rapp-commons-event/1.0 post
```
