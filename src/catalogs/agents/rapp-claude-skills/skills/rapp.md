# RAPP Pipeline Skill

Execute the full RAPP (Rapid Agent Prototype Platform) pipeline.

## Trigger
`/rapp`

## Description
The RAPP skill orchestrates the complete agent development lifecycle - from discovery transcripts to deployed, production-ready AI agents.

## Actions

### transcript_to_agent
Generate a complete agent from a transcript.

**Parameters:**
- `transcript` - Inline transcript text OR path to file
- `project_id` - Project identifier for output organization
- `customer_name` - Customer/company name for context
- `agent_priority` - Which agent to prioritize (e.g., 'assistant', 'analyst')

**Example:**
```
/rapp transcript_to_agent
  --transcript "Customer wants a chatbot for FAQ..."
  --project_id "acme-faq"
  --customer_name "Acme Corp"
```

### auto_process
Automatically scan project inputs and process all files.

**Parameters:**
- `project_id` - Project folder to scan

### generate_report
Create professional PDF reports.

**Parameters:**
- `project_id` - Project to report on
- `report_type` - discovery, mvp, code, qg1-qg6, executive_summary

## Pipeline Steps

1. **Discovery** - Parse transcripts, extract requirements
2. **MVP Design** - Define scope, prioritize features
3. **Code Generation** - Create agent Python code
4. **Quality Gates** - Validate through QG1-QG6
5. **Deployment** - Deploy to Azure Functions
6. **Iteration** - Continuous improvement loop

## Output Structure

```
rapp_projects/{project_id}/
├── inputs/           # Source transcripts, feedback
├── outputs/          # Generated agents, demos, reports
│   ├── {agent}_agent.py
│   ├── {agent}_demo.json
│   ├── agent_tester.html
│   └── *.pdf reports
└── metadata.json     # Project tracking
```

## Integration

This skill integrates with:
- **CommunityRAPP** - Backend API for agent execution
- **RAR** - Publishes generated agents to the [RAPP Agent Registry](https://github.com/kody-w/RAR)
- **[rapp-commons](https://github.com/kody-w/rapp-commons)** - Announces new agents on the social layer via a signed `rapp-commons-event/1.0` post over the resident

## Quality Gates

| Gate | Validation |
|------|------------|
| QG1 | Discovery completeness |
| QG2 | MVP scope clarity |
| QG3 | Code structure |
| QG4 | Test coverage |
| QG5 | Security review |
| QG6 | Deployment readiness |
