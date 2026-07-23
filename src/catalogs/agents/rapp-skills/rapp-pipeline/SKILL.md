---
name: rapp-pipeline
description: Run RAPP (Rapid Agent Prototyping Platform) pipeline to generate AI agents from transcripts. Use when building agents, generating Copilot Studio solutions, or deploying to Microsoft AI stack.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# RAPP Pipeline Skill

This skill runs the RAPP pipeline to generate production-ready AI agents from business transcripts.

## Available Commands

### Full Pipeline (Transcript to Agent)
```bash
python3 -m rapp_cli pipeline <project_id> [options]
```

Options:
- `-t, --transcript PATH` - Path to transcript file
- `-c, --customer TEXT` - Customer name
- `-o, --output PATH` - Output directory
- `--json-output` - Output results as JSON (for parsing)

### Copilot Studio + Azure DevOps
```bash
python3 -m rapp_cli copilot-studio <project_id> [options]
```

Options:
- `-t, --transcript PATH` - Path to transcript file
- `-c, --customer TEXT` - Customer name
- `-p, --publisher TEXT` - Solution publisher prefix
- `-e, --environments TEXT` - Target environments (comma-separated)
- `--json-output` - Output results as JSON

### Project Management
```bash
# List all projects
python3 -m rapp_cli list-projects --json-output

# Show project details
python3 -m rapp_cli show-project <project_id> --json-output

# Create new project
python3 -m rapp_cli new <project_name>
```

### Quality Gates
```bash
python3 -m rapp_cli quality-gate <project_id> --gate QG1
```

Gates: QG1 (Transcript), QG2 (Customer), QG3 (Code), QG4-QG5 (Demo), QG6 (Deployment)

### Reports
```bash
python3 -m rapp_cli report <project_id> --report-type discovery
```

Types: discovery, mvp, code, qg1-qg6, executive_summary

## Workflow

1. **Create Project**
   ```bash
   python3 -m rapp_cli new my-project
   ```

2. **Add Transcript** (save to `rapp_projects/{project}/inputs/transcript.txt`)

3. **Run Pipeline**
   ```bash
   # Basic agent generation
   python3 -m rapp_cli pipeline my-project --customer "Contoso" --json-output

   # Full Microsoft AI stack
   python3 -m rapp_cli copilot-studio my-project --customer "Contoso" --json-output
   ```

4. **Check Output**
   ```bash
   python3 -m rapp_cli show-project my-project --json-output
   ```

## Output Locations

- Agents: `rapp_projects/{project}/outputs/{agent_id}_agent.py`
- Demos: `rapp_projects/{project}/outputs/{agent_id}_demo.json`
- HTML Tester: `rapp_projects/{project}/outputs/agent_tester.html`
- Copilot Studio: `rapp_projects/{project}/copilot_studio/`
- Azure DevOps: `rapp_projects/{project}/azure_devops/`

## Working Directory

Always run commands from: `~/.rapp/src`

## Example: End-to-End Automation

```bash
cd ~/.rapp/src

# 1. Create project
python3 -m rapp_cli new contoso-agent

# 2. Create transcript (or use existing)
cat > rapp_ai/rapp_projects/contoso-agent/inputs/transcript.txt << 'EOF'
[Discovery call transcript content here]
EOF

# 3. Run full pipeline
python3 -m rapp_cli copilot-studio contoso-agent \
  --customer "Contoso Financial" \
  --publisher contoso \
  --environments "dev,test,prod" \
  --json-output

# 4. Verify outputs
python3 -m rapp_cli show-project contoso-agent --json-output
```
