# RAPP Starter Template

A minimal boilerplate for building RAPP AI implementations with best practices baked in.

## Quick Start

```bash
# Clone
git clone https://github.com/kody-w/RAPP_Hub.git
cd RAPP_Hub/implementations/rapp-starter-template

# Setup
pip install -r requirements.txt

# Run
python main.py
```

## Project Structure

```
rapp-starter-template/
├── rapp.json           # RAPP Hub manifest (dependencies, metadata)
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── agents/
│   ├── basic_agent.py  # Base class for all agents
│   └── example_agent.py # Example agent (replace with your own)
└── README.md
```

## Adding Agents

### From RAPP Store

```bash
# Install the RAPP Hub CLI
pip install rapp-hub

# Add agents from RAPP Store
rapp-hub deps add pdf_processor_agent
rapp-hub deps add email_assistant_agent

# Or add skills
rapp-hub deps add algorithmic-art --type skill
```

### Custom Agents

Create a new file in `agents/` following this pattern:

```python
from agents.basic_agent import BasicAgent

class MyCustomAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyCustom'
        self.metadata = {
            "name": self.name,
            "description": "What my agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action')
        # Your logic here
        return "Result"
```

## Configuration

Set environment variables:

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4"  # optional
export RAPP_APP_NAME="My App"  # optional
export RAPP_DEBUG="true"  # optional
```

## Next Steps

1. **Add agents** from RAPP Store or create custom ones
2. **Implement AI routing** - replace simple keyword matching with OpenAI function calling
3. **Add persistence** - connect to a database or file storage
4. **Deploy** - containerize or deploy to Azure Functions

## Resources

- [RAPP Hub](https://kody-w.github.io/RAPP_Hub/) - Find complete implementations
- [RAPP Store](https://kody-w.github.io/RAPP_Store/) - Browse agents and skills
- [Protocol Docs](https://github.com/kody-w/RAPP_Hub/blob/main/docs/PROTOCOL.md)
