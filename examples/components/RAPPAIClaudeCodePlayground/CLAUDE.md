# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Copilot Agent 365** - an enterprise AI assistant built on Azure Functions with GPT-4, featuring persistent memory and a modular agent system. The application provides a serverless chatbot with conversation memory that persists across sessions using Azure File Storage.

## Development Commands

### Local Development

**Start the function app locally:**
```bash
# Mac/Linux
./run.sh

# Windows
.\run.ps1
```

The local function will be available at:
- API: `http://localhost:7071/api/businessinsightbot_function`
- Web Interface: Open `index.html` in a browser

**Install dependencies:**
```bash
# Create virtual environment (Python 3.9-3.11 required, NOT 3.13+)
python3.11 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# or
.venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

**Azure Functions Core Tools:**
```bash
npm install -g azure-functions-core-tools@4
```

### Testing

**Test locally with curl:**
```bash
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

**Test locally with PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:7071/api/businessinsightbot_function" `
  -Method Post `
  -Body '{"user_input": "Hello", "conversation_history": []}' `
  -ContentType "application/json"
```

### Deployment

**Deploy to Azure (requires Azure CLI):**
```bash
# First login
az login

# Then deploy using the script
./deploy.sh
```

## Architecture

### Core Components

**function_app.py** - Main Azure Function entry point
- HTTP-triggered function `businessinsightbot_function`
- Handles request/response with CORS support
- Manages conversation flow and agent execution
- Contains `Assistant` class which orchestrates:
  - OpenAI API calls with function calling
  - Agent discovery and loading (both local and from Azure File Storage)
  - Memory management (shared and user-specific via GUID)
  - Response formatting with separate "formatted" and "voice" outputs

**Agent System** - Modular, extensible AI agents
- All agents inherit from `agents/basic_agent.py::BasicAgent`
- Agents are auto-discovered from:
  1. Local `agents/` directory
  2. Azure File Storage `agents/` directory (loaded at runtime from `/tmp/agents`)
  3. Azure File Storage `multi_agents/` directory (loaded at runtime from `/tmp/multi_agents`)
- Each agent exposes metadata for OpenAI function calling
- Key agents:
  - `ContextMemoryAgent` - Retrieves stored memories (shared or user-specific)
  - `ManageMemoryAgent` - Stores new memories with themes and timestamps

**Memory Architecture** (Critical Design Pattern)
- **Dual-context memory system** using Azure File Storage:
  - **Shared memories**: `shared_memories/memory.json` - accessible to all users
  - **User-specific memories**: `memory/{GUID}/user_memory.json` - per-user context
- Memory context is set via GUID (validated UUID format)
- Default GUID: `c0p110t0-aaaa-bbbb-cccc-123456789abc` used when no user GUID provided
- `AzureFileStorageManager` handles context switching via `set_memory_context(guid)`
- Memory is loaded at Assistant initialization and updated during conversation
- GUID can be passed via:
  - First message in conversation_history (if entire message is just a GUID)
  - `user_input` parameter (if entire input is just a GUID)
  - `user_guid` field in request body

**Storage Layer** - `utils/azure_file_storage.py`
- `AzureFileStorageManager` class manages all Azure File Storage operations
- Handles both text and binary files
- Supports nested directory structures
- Memory context tracking with `current_guid` and `current_memory_path`
- SAS token generation for temporary file URLs

### Request/Response Flow

1. HTTP request received by `businessinsightbot_function`
2. Extract `user_input`, `conversation_history`, optional `user_guid`
3. Load agents from local and Azure File Storage
4. Create `Assistant` instance
5. Initialize memory context (shared + user-specific if GUID provided)
6. `Assistant.get_response()` processes the request:
   - Prepare messages with system prompt including memory context
   - Call OpenAI with function metadata from all agents
   - If function_call returned, execute agent and loop
   - Parse final response into `formatted_response` and `voice_response`
7. Return JSON with both responses + agent logs + user_guid

### Response Format Convention

The system prompt enforces a dual-output format:
- **Formatted response** (before `|||VOICE|||`): Full markdown with formatting
- **Voice response** (after `|||VOICE|||`): 1-2 sentence plain text summary for TTS

Example:
```
Here's the detailed analysis:

**Key Findings:**
- Revenue increased by 12%

|||VOICE|||
Revenue's up 12 percent - looking good.
```

### Agent Development

**Creating a new agent** in `agents/my_agent.py`:

```python
from agents.basic_agent import BasicAgent

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyAgent'
        self.metadata = {
            "name": self.name,
            "description": "What this agent does for OpenAI function calling",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        input_data = kwargs.get('input', '')
        # Your logic here
        return f"Result: {input_data}"
```

Agents are automatically discovered on next function cold start.

### Configuration

**Environment Variables** (set in `local.settings.json` locally, or Azure Function App Configuration for production):

Required:
- `AzureWebJobsStorage` - Azure Storage connection string
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Name of GPT model deployment (default: `gpt-deployment`)
- `AZURE_FILES_SHARE_NAME` - Azure File Share name (default: `azfbusinessbot3c92ab`)

Optional:
- `ASSISTANT_NAME` - Bot's name (default: `BusinessInsightBot`)
- `CHARACTERISTIC_DESCRIPTION` - Bot's personality (default: `helpful business assistant`)
- `AZURE_OPENAI_API_VERSION` - API version (default: `2024-02-01`)

**IMPORTANT: Never commit `local.settings.json` to Git** - it contains secrets.

## File Structure

```
/
├── function_app.py          # Main Azure Function with Assistant class
├── agents/                  # Local agent definitions
│   ├── basic_agent.py      # Base agent class
│   ├── context_memory_agent.py
│   └── manage_memory_agent.py
├── utils/
│   └── azure_file_storage.py  # Storage manager with memory context
├── requirements.txt         # Python dependencies (pinned versions)
├── host.json               # Azure Functions v4 configuration
├── index.html              # Web chat UI
├── run.sh / run.ps1        # Local development scripts
├── deploy.sh               # Azure deployment script
└── local.settings.json     # Local config (NOT in git)
```

## Key Technical Details

**Python Version**: Use Python 3.9-3.11 only. Python 3.13+ causes Azure Functions compatibility issues.

**Azure Functions Version**: v4 (see `host.json`)

**OpenAI Integration**: Uses `openai==1.55.3` with `AzureOpenAI` client and function calling.

**CORS**: Handled in `build_cors_response()` - allows all origins with credentials.

**Memory Limits**:
- Conversation history trimmed to last 20 messages to prevent memory issues (function_app.py:484)
- Shared memory limited to 5000 characters (function_app.py:279)
- User memory limited to 5000 characters (function_app.py:293)

**Retry Logic**: OpenAI calls have 3 retries with 2-second delay (function_app.py:479)

**Error Handling**: All function parameters sanitized to handle None values and convert to strings (function_app.py:545-551)

**Agent Loading**: Dynamically loads agents from Azure File Storage to `/tmp/` directories with module system integration (function_app.py:103-205)
