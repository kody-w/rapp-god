---
name: fy27-priority-agents
description: >
  Regenerate the FY27 Priority Agents report (cross-customer analysis) with the
  LATEST data. USE THIS SKILL when the user asks to "run the FY27 report",
  "refresh the priority agents report", "re-pull the agent scenarios",
  "get the latest customer agents", "rerun the agent sweep", or anything about
  the triage-chat corpus / scenario worksheets / customer agent roster. It
  enumerates every customer with a triage chat, extracts each one's named agents
  + business problems via the local query CLI, verifies the results, and renders
  the report in the original HTML style on the Desktop.
---

# FY27 Priority Agents — refresh pipeline

Regenerates the FY27 Priority Agents report from live data. The hard part is
that **the query CLI (an M365 Copilot / Graph-grounded tool) is slow and flaky**;
this skill encodes the exact recipe + lessons that make it work. Everything lives
in the durable working dir:

```
WORKDIR = ~/.brainstem/agent-scenario-sweep/
```

Run all python with the brainstem venv: `~/.brainstem/venv/bin/python`.

## Prerequisites (check first)
- Query CLI installed & authenticated: `<cli> ask -q "Reply with exactly: PONG"`
  should return `PONG` in <60s. If it times out, M365 is throttled (see Lessons) — wait.
- `WORKDIR/template_original.html` exists (the original report, used as the literal
  render template). If missing, ask the user for the original report HTML.
- `WORKDIR/roster_full.json` exists (the full account roster). If the user provides
  an updated roster spreadsheet, rebuild it (see "Updating the roster").

## The pipeline (run in order)

**1. Extract — one grounded query per account, PARALLEL=4, resumable.**
```
cd ~/.brainstem/agent-scenario-sweep
bash run_until_done.sh          # wraps extract_agents.py; auto-resumes through throttle
```
- Writes raw verbatim response per account to `extract/<CUSTOMER>.json` (the audit trail
  + re-run/compare source). Resumable: re-running skips done accounts.
- `extract_agents.py` uses PARALLEL=4 (proven safe), escalating timeouts (150/220/320s),
  retries flaky "retrieval_fail"/bare-NONE responses, and only cools down if a PONG
  actually confirms a throttle. Full run ≈ 1–3 hrs depending on throttling.
- The query is **grounded**: "looking ONLY at the internal triage chat for X
  + the scenario worksheet, what agents did X name?" — this prevents the tool from
  hallucinating a vendor's public product announcements (it once returned a
  customer's public products instead of their internal agents).

**2. Verify with the 1M context (THE critical quality step — do NOT skip).**
The regex parser (`parse_agents.py`) is unreliable: it both misses real agents and
counts verbose-NONEs as has-agents. Instead, dump the candidate responses and READ them:
```
~/.brainstem/venv/bin/python - <<'PY'
import glob,json,re
rows=[]
for f in sorted(glob.glob("extract/*.json")):
    d=json.load(open(f))
    if d.get("status")!="ok": continue
    r=d.get("response","")
    if len(r.strip())>120 and not re.fullmatch(r"\W*NONE\W*", r.strip(), re.I):
        rows.append((d["customer"], r))
open("/tmp/fy27_candidates.txt","w").write(
    "".join(f"\n{'='*70}\nCUSTOMER: {c}\n{'='*70}\n{r}\n" for c,r in rows))
print(f"{len(rows)} candidates -> /tmp/fy27_candidates.txt")
PY
```
Then Read `/tmp/fy27_candidates.txt` (in pages) and hand-build `verified_agents.json`,
applying these rules (this is judgment the regex cannot do):
- **Keep** only agents explicitly named in the customer's OWN triage chat / worksheet.
- **Drop verbose-NONEs**: responses that explain at length then end in "Final Answer: NONE"
  / "Result: NONE" (several accounts had a chat that was intake-only).
- **Strip worksheet template-examples**: "Sales AI Agent" and "Time-tracker Agent" are
  the blank worksheet's built-in example rows — exclude unless clearly customer-specific.
- **Drop deck/PPTX-sourced agents** — not from the chat/worksheet.
- **Merge casing/name dupes.**
`verified_agents.json` shape: `{"customers": {"<name>": [{"agent","problem"}, ...]}}`.

**3. Build the report (original style, data expanded).**
```
~/.brainstem/venv/bin/python build_final.py
open ~/Desktop/FY27-Priority-Agents-FINAL.html
```
This uses `template_original.html` verbatim and only ADDS data: appends verified agent
rows to the Raw Data tab, adds fresh customer cards to By Customer, adds a "Full Roster"
tab showing every account checked + status (so nothing looks skipped), bumps the stats,
and fixes pill wrapping. Visual style is unchanged — the stakeholder wants it to look
identical.

**4. Sanity-check before sending.** Confirm: all original tabs present, the original
customer set still shown, fresh customers have real agents, roster lists every account.

## Lessons (why the pipeline is shaped this way — respect these)
- **Run via the query CLI directly, NOT through the brainstem `/chat`.** The brainstem
  is threaded AND decomposes one /chat into multiple sub-calls → a batch becomes
  60+ concurrent processes → throttles the whole M365 account for 30+ min.
- **PARALLEL=4 is the safe ceiling.** 4 concurrent direct calls tested clean
  (~55s for 4, PONG fine after). Concurrency >~6 risks throttle. Never fan out wide.
- **Mimic the agent's invocation:** `subprocess.run([...], capture_output,
  text, timeout)` + strip ANSI + reap the whole process group on timeout (the CLI
  spawns nested node children that orphan otherwise and cause throttling). See `wq.py`.
- **"not found" in a prior roster ≠ no agents.** Always re-run every account fresh; the
  grounded query returns NONE itself if there's genuinely nothing.
- **Bare 4-char "NONE" = flaky retrieval, not a real NONE.** A genuine NONE is verbose
  ("I searched X, found no worksheet…"). Retry bare-NONEs.
- **Most accounts that HAD a chat were intake-only** (worksheet requested, never filled).
  A result of a small fraction of customers with agents is correct, not a failure — the
  denominator of accounts that actually named agents is small. Don't chase a bigger number.
- **Keep everything in `~/.brainstem/agent-scenario-sweep/`, NOT `.brainstem_data/`** —
  the brainstem wipes `.brainstem_data/` on restart (it ate a sweep mid-run once).
- **If throttled:** stop all CLI processes, wait ~20–30 min, PONG-probe
  until it returns, then resume (`run_until_done.sh` is resumable).

## Updating the roster (when the customer list grows)
If the user provides a fresh roster spreadsheet (the sheet listing every triage chat
per customer), rebuild `roster_full.json` from it: read the sheet with openpyxl, keep
`customer` + `chat` columns, then re-run the pipeline. The extractor reads
`roster_full.json` and runs every account.

## Files in WORKDIR
- `wq.py` — direct CLI runner (mimics the agent; process-group reaping)
- `extract_agents.py` — PARALLEL=4 grounded extraction, resumable, throttle-guarded
- `run_until_done.sh` — self-resuming wrapper around the extractor
- `build_final.py` — renders the final report from `template_original.html` + `verified_agents.json`
- `verified_agents.json` — the hand-verified agent data (rebuilt each run in step 2)
- `roster_full.json` — full account roster
- `template_original.html` — the original report, used as the render template
- `extract/*.json` — raw verbatim responses (audit trail)

## Output
`~/Desktop/FY27-Priority-Agents-FINAL.html` — share-ready, single self-contained file.
