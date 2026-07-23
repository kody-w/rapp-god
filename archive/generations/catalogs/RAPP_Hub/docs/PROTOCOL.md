# RAPP Hub Protocol Specification v1.0

This document defines the protocol for RAPP Hub - a registry for complete AI implementations that can depend on RAPP Store agents and skills.

## Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAPP ECOSYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     RAPP Hub                             │   │
│  │            (Implementation Registry)                     │   │
│  │                                                          │   │
│  │  • Complete AI applications                              │   │
│  │  • Declare dependencies on RAPP Store                    │   │
│  │  • User-published implementations                        │   │
│  │  • Quickstart templates                                  │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           │ depends on                          │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    RAPP Store                            │   │
│  │                (Agent/Skill Registry)                    │   │
│  │                                                          │   │
│  │  • Individual agents (Python classes)                    │   │
│  │  • Individual skills (Markdown instructions)             │   │
│  │  • Versioned packages                                    │   │
│  │  • Cross-format conversion                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**RAPP Store** = Individual agents and skills (like npm packages)
**RAPP Hub** = Complete implementations (like full applications on GitHub)

## User Flow

### Creating a New Implementation

```
1. Initialize    rapp-hub init my-project
       │
       ▼
2. Develop      Add custom agents, business logic
       │
       ▼
3. Add Deps     rapp-hub deps add pdf_processor_agent
       │
       ▼
4. Test         python main.py
       │
       ▼
5. Publish      Push to GitHub
       │
       ▼
6. Register     rapp-hub publish → Submit to RAPP Hub
```

### Installing an Implementation

```
1. Browse       rapp-hub browse (or visit web UI)
       │
       ▼
2. Install      rapp-hub install copilot-entra-agent
       │
       ▼
3. Auto-resolves RAPP Store dependencies
       │
       ▼
4. Run          python main.py
```

## Manifest Specification

### RAPP Hub manifest.json

```json
{
  "$schema": "https://rapp-hub.github.io/schema/v1/manifest.json",
  "version": "1.0.0",
  "hub": {
    "name": "RAPP Hub",
    "description": "Central registry for RAPP implementations",
    "owner": "github-username",
    "url": "https://github.com/username/RAPP_Hub",
    "license": "Apache-2.0"
  },
  "protocol": {
    "version": "1.0",
    "type": "rapp-hub",
    "store_registry": "https://raw.githubusercontent.com/kody-w/RAPP_Store/main/manifest.json",
    "compatible_stores": [...]
  },
  "categories": [...],
  "implementations": [...]
}
```

### Implementation Entry

```json
{
  "id": "unique-implementation-id",
  "name": "Human Readable Name",
  "description": "What this implementation does",
  "version": "1.0.0",
  "category": "category-id",
  "author": "Author Name",
  "license": "Apache-2.0",
  "repo": "https://github.com/owner/repo",
  "path": "path/within/repo",
  "branch": "main",
  "icon": "🤖",
  "tags": ["tag1", "tag2"],
  "features": ["Feature 1", "Feature 2"],
  "stack": {
    "runtime": "python",
    "version": "3.11",
    "platform": "azure-functions",
    "ai": "azure-openai"
  },
  "dependencies": {
    "rapp_store": {
      "agents": ["agent_id@^1.0.0"],
      "skills": ["skill-id@latest"]
    },
    "python": ["openai>=1.0.0"]
  },
  "quickstart": {
    "clone": "git clone command",
    "setup": "setup command",
    "run": "run command"
  }
}
```

## rapp.json Specification

Every RAPP implementation should include a `rapp.json` at its root:

```json
{
  "name": "my-implementation",
  "version": "1.0.0",
  "description": "What this implementation does",
  "author": "Your Name",
  "license": "Apache-2.0",
  "repository": "https://github.com/you/your-repo",
  "category": "enterprise",
  "icon": "🤖",
  "tags": ["tag1", "tag2"],
  "features": [
    "Feature 1",
    "Feature 2"
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
      "skills": ["algorithmic-art@latest"]
    },
    "python": ["openai>=1.0.0", "pandas>=2.0.0"]
  },
  "scripts": {
    "setup": "pip install -r requirements.txt",
    "start": "python main.py",
    "test": "pytest"
  }
}
```

## Dependency Resolution

### Version Constraints

| Constraint | Meaning | Example |
|------------|---------|---------|
| `^1.0.0` | Compatible with 1.x.x | >=1.0.0 <2.0.0 |
| `~1.0.0` | Patch-level only | >=1.0.0 <1.1.0 |
| `1.0.0` | Exact version | =1.0.0 |
| `latest` | Latest available | Most recent |
| `*` | Any version | Any |

### Resolution Process

```
1. Parse rapp.json dependencies
2. For each RAPP Store agent/skill:
   a. Fetch RAPP Store manifest
   b. Find matching version
   c. Download to agents/ or skills/ directory
3. For each Python dependency:
   a. Install via pip
```

### Directory Structure

After dependency installation:

```
my-implementation/
├── rapp.json
├── main.py
├── requirements.txt
├── agents/
│   ├── basic_agent.py          # Base class
│   ├── my_custom_agent.py      # Your agents
│   ├── pdf_processor_agent.py  # From RAPP Store
│   └── email_assistant_agent.py # From RAPP Store
├── skills/
│   └── algorithmic-art/
│       └── SKILL.md            # From RAPP Store
└── ...
```

## Publishing Protocol

### Option 1: Pull Request (Recommended)

1. Fork `https://github.com/kody-w/RAPP_Hub`
2. Add entry to `manifest.json` implementations array
3. Submit Pull Request
4. Maintainers review and merge

### Option 2: Self-Registration

Create `.rapp-hub.json` in your repository root:

```json
{
  "id": "your-implementation-id",
  "name": "Your Implementation",
  "description": "...",
  ...
}
```

Discovery via: `https://raw.githubusercontent.com/you/repo/main/.rapp-hub.json`

### Option 3: External Registry

Host your own RAPP Hub manifest and register it:

```json
{
  "external_registries": [
    "https://raw.githubusercontent.com/company/rapp-hub/main/manifest.json"
  ]
}
```

## Categories

| ID | Name | Use For |
|----|------|---------|
| `enterprise` | Enterprise Solutions | Production business AI |
| `copilot` | Copilot Integrations | M365/Teams integration |
| `automation` | Workflow Automation | Business process automation |
| `analytics` | Analytics & Insights | Data analysis, BI |
| `customer-service` | Customer Service | Support, service desk |
| `developer-tools` | Developer Tools | Dev/DevOps tooling |
| `starter` | Starter Templates | Boilerplate templates |

## CLI Reference

### Initialize Project

```bash
rapp-hub init <project-name> [--template <template>]
```

Creates new project from starter template.

### Dependency Management

```bash
# Install all dependencies from rapp.json
rapp-hub deps install

# Add agent from RAPP Store
rapp-hub deps add <agent-id>

# Add skill from RAPP Store
rapp-hub deps add <skill-id> --type skill

# Update dependencies
rapp-hub deps update
```

### Publishing

```bash
# Generate RAPP Hub registration entry
rapp-hub publish
```

### Discovery

```bash
# Browse implementations
rapp-hub browse [--category <category>]

# Search implementations
rapp-hub search <query>

# Get implementation details
rapp-hub info <impl-id>

# Install implementation
rapp-hub install <impl-id>
```

## Security Considerations

1. **Code Review**: All PR submissions reviewed before merge
2. **Dependency Audit**: RAPP Store agents verified
3. **Version Pinning**: Pin versions in production
4. **License Compliance**: Check licenses of dependencies
5. **No Auto-Execution**: Never auto-execute downloaded code

## API Endpoints

All endpoints via raw GitHub:

| Endpoint | Description |
|----------|-------------|
| `/manifest.json` | Hub manifest with all implementations |
| `/implementations/{id}/rapp.json` | Implementation metadata |
| `/{store}/manifest.json` | RAPP Store manifest |
| `/{store}/agents/{id}/{file}` | Agent source code |
| `/{store}/skills/{id}/SKILL.md` | Skill definition |

## Compatibility

### Supported Platforms

- Standalone Python applications
- Azure Functions
- AWS Lambda
- Docker containers
- Kubernetes

### Supported AI Providers

- OpenAI
- Azure OpenAI
- Anthropic Claude
- Local models (Ollama, etc.)

## Versioning

Protocol follows semantic versioning:
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes

Current version: **1.0**
