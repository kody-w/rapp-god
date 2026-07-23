# Contributing to RAPP Hub

Thank you for your interest in contributing to RAPP Hub! This guide covers how to publish your own RAPP implementation and contribute to the ecosystem.

## Publishing Your Implementation

### Step 1: Create Your Project

```bash
# Initialize from template
rapp-hub init my-awesome-project
cd my-awesome-project

# Or start from scratch with rapp.json
```

### Step 2: Develop Your Implementation

```
my-awesome-project/
├── rapp.json           # Required: Project manifest
├── main.py             # Entry point
├── README.md           # Documentation
├── requirements.txt    # Python dependencies
├── agents/
│   ├── basic_agent.py  # Base class
│   └── your_agent.py   # Your custom agents
└── ...
```

### Step 3: Add RAPP Store Dependencies

```bash
# Add agents from RAPP Store
rapp-hub deps add pdf_processor_agent
rapp-hub deps add email_assistant_agent

# Add skills
rapp-hub deps add algorithmic-art --type skill
```

### Step 4: Configure rapp.json

```json
{
  "name": "my-awesome-project",
  "version": "1.0.0",
  "description": "Clear description of what your implementation does",
  "author": "Your Name",
  "license": "Apache-2.0",
  "repository": "https://github.com/you/my-awesome-project",
  "category": "automation",
  "icon": "🚀",
  "tags": ["automation", "ai", "workflow"],
  "features": [
    "Feature 1 - what it does",
    "Feature 2 - what it does"
  ],
  "stack": {
    "runtime": "python",
    "version": "3.11",
    "platform": "standalone",
    "ai": "openai"
  },
  "dependencies": {
    "rapp_store": {
      "agents": ["pdf_processor_agent@^1.0.0"],
      "skills": []
    },
    "python": ["openai>=1.0.0"]
  },
  "scripts": {
    "setup": "pip install -r requirements.txt",
    "start": "python main.py",
    "test": "pytest"
  }
}
```

### Step 5: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/you/my-awesome-project.git
git push -u origin main
```

### Step 6: Register in RAPP Hub

```bash
# Generate registration entry
rapp-hub publish
```

This creates `.rapp-hub-entry.json` with your registration data.

**Option A: Pull Request (Recommended)**

1. Fork https://github.com/kody-w/RAPP_Hub
2. Add your entry to `manifest.json` implementations array
3. Submit Pull Request

**Option B: Issue Request**

1. Open issue at https://github.com/kody-w/RAPP_Hub/issues
2. Paste your `.rapp-hub-entry.json` content
3. Request registration

**Option C: Self-Registration**

1. Add `.rapp-hub.json` to your repository root
2. Your repo is discoverable via direct URL

## Implementation Requirements

### Required Files

| File | Purpose |
|------|---------|
| `rapp.json` | Project manifest with metadata and dependencies |
| `README.md` | Documentation with setup instructions |
| `main.py` (or entry point) | Application entry point |

### Recommended Structure

```
your-project/
├── rapp.json           # Manifest
├── README.md           # Documentation
├── main.py             # Entry point
├── requirements.txt    # Python deps
├── agents/
│   ├── basic_agent.py  # Base class
│   └── *.py            # Your agents
├── skills/             # Optional: Claude skills
├── tests/              # Optional: Tests
└── docs/               # Optional: Extra docs
```

### Quality Checklist

- [ ] Clear, descriptive `rapp.json`
- [ ] README with setup instructions
- [ ] Working quickstart commands
- [ ] All dependencies declared
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Code is documented

## Categories

Choose the appropriate category:

| Category | Use For |
|----------|---------|
| `enterprise` | Production business solutions |
| `copilot` | Microsoft 365/Teams integrations |
| `automation` | Workflow and process automation |
| `analytics` | Data analysis and BI |
| `customer-service` | Support and helpdesk |
| `developer-tools` | Development tooling |
| `starter` | Templates and boilerplates |

## Dependency Guidelines

### Declaring RAPP Store Dependencies

```json
{
  "dependencies": {
    "rapp_store": {
      "agents": [
        "pdf_processor_agent@^1.0.0",
        "email_assistant_agent@latest"
      ],
      "skills": [
        "algorithmic-art@^1.0.0"
      ]
    }
  }
}
```

### Version Constraints

- `^1.0.0` - Compatible updates (1.x.x)
- `~1.0.0` - Patch updates only (1.0.x)
- `1.0.0` - Exact version
- `latest` - Always latest
- `*` - Any version

### Best Practices

1. **Pin major versions** for stability
2. **Use `latest` only** for development
3. **Test with pinned versions** before publishing
4. **Document required agents** in README

## Creating Agents for RAPP Store

If you create useful agents, consider contributing them to RAPP Store:

### Agent Template

```python
from agents.basic_agent import BasicAgent

class MyUsefulAgent(BasicAgent):
    """
    Clear docstring explaining what this agent does.
    """

    def __init__(self):
        self.name = 'MyUseful'
        self.metadata = {
            "name": self.name,
            "description": "What this agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["action1", "action2"]
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action')
        # Implementation
        return "Result"
```

### Submit to RAPP Store

1. Fork https://github.com/kody-w/RAPP_Store
2. Add agent to `agents/your_agent/your_agent.py`
3. Add entry to `manifest.json`
4. Submit Pull Request

## Code of Conduct

- Be respectful and constructive
- Write clear documentation
- Test before submitting
- No malicious code
- Follow license requirements

## Getting Help

- **Issues**: https://github.com/kody-w/RAPP_Hub/issues
- **Discussions**: https://github.com/kody-w/RAPP_Hub/discussions
- **RAPP Store**: https://github.com/kody-w/RAPP_Store

## License

By contributing, you agree that your contributions will be licensed under Apache 2.0.

Thank you for contributing to the RAPP ecosystem!
