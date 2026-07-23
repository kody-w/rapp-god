# RAPP Pipeline Agent

Orchestrates the complete RAPP methodology for agent development.

## Agent Type
`rapp-pipeline`

## Description
This agent manages the 14-step RAPP pipeline from discovery through deployment, coordinating with other agents and maintaining project state.

## Capabilities
- Parse discovery transcripts
- Generate MVP documents
- Create agent code
- Execute quality gates (QG1-QG6)
- Deploy to Azure Functions
- Generate professional reports

## Usage

Invoke via Task tool:
```
subagent_type: "rapp-pipeline"
prompt: "Process transcript for Acme Corp chatbot project"
```

## Pipeline Steps

### Phase 1: Discovery (Steps 1-3)
1. Prepare discovery call agenda
2. Process transcript
3. Generate discovery summary

### Phase 2: MVP Design (Steps 4-6)
4. Generate MVP proposal
5. Prioritize features
6. Define scope and timeline

### Phase 3: Development (Steps 7-9)
7. Generate agent code
8. Create agent metadata
9. Generate tests

### Phase 4: Quality (Steps 10-12)
10. Execute QG1-QG3 (structure)
11. Execute QG4-QG5 (function)
12. Execute QG6 (deployment)

### Phase 5: Deploy (Steps 13-14)
13. Deploy to Azure
14. Generate documentation

## Input Detection

The agent auto-detects input types:
- `transcript*.txt` → Discovery processing
- `feedback*.txt` → Customer validation
- `*.py` → Code review
- `metrics*.json` → Deployment analysis

## Output

All outputs go to `rapp_projects/{project_id}/outputs/`:
- Agent code (.py)
- Demo data (.json)
- Test files (_test.py)
- HTML tester
- PDF reports

## State Management

Project state persisted in:
```json
{
  "project_id": "project-name",
  "customer": "Customer Name",
  "current_step": 7,
  "completed_gates": ["QG1", "QG2", "QG3"],
  "agents_generated": ["assistant", "analyst"],
  "last_updated": "2026-01-30T12:00:00Z"
}
```

## Integration Points

- **CommunityRAPP**: Deploys agents to function_app.py
- **RAR**: Publishes generated agents to the [RAPP Agent Registry](https://github.com/kody-w/RAR)
- **[rapp-commons](https://github.com/kody-w/rapp-commons)**: Announces new agents on the social layer via a signed `rapp-commons-event/1.0` post over the resident (rapp-god-forum for threaded discussion)
