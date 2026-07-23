---
name: deep-research
description: Performs rigorous, evidence-first deep research using distinct parallel research strategies, primary sources, local artifacts, controlled experiments, adversarial verification, and confidence-rated synthesis. Use when a user asks for deep research, exhaustive investigation, reverse engineering, current landscape analysis, high-stakes comparison, or a defensible implementation recommendation.
license: MIT
compatibility: Works with Agent Skills-compatible systems. Benefits from web/file search and parallel subagents, but includes a sequential fallback.
metadata:
  author: kody-w
  version: "1.0.0"
  rapp-target: deep_research_agent.py
---

# Deep Research

Produce a decision-grade answer whose important claims can be traced to
evidence. Do not confuse a long answer, many agents, or majority agreement with
research quality.

## Inputs

Treat the user's request, invocation arguments, or `$ARGUMENTS` as `QUERY`.
Derive:

- the exact question and requested decision or artifact;
- scope, exclusions, and relevant time horizon;
- freshness requirements;
- the evidence needed to call the result complete;
- safety, privacy, copyright, and authorization boundaries.

Make reasonable assumptions and proceed. Ask a question only when an answer is
required to avoid unsafe work or materially different outcomes.

## Research contract

1. Report only claims supported by cited sources, inspected artifacts, or
   recorded experiments.
2. Separate **observed**, **documented**, **inferred**, **disputed**, and
   **unknown** claims.
3. Prefer primary evidence. Never invent citations or cite a search-result
   snippet as if it were the underlying source.
4. Use independent tracks with non-overlapping scopes. Do not send multiple
   agents to repeat the same search.
5. Treat convergence as a prioritization signal, not proof. Verify
   majority-supported conclusions against evidence.
6. Preserve minority findings when they identify a concrete contradiction,
   failure mode, or missing assumption.
7. Do not expose credentials, private data, proprietary source, or copyrighted
   material beyond what is necessary for analysis.
8. State blockers and evidence gaps plainly. Never make a partial result look
   complete.

## Step 1: Frame the investigation

Write a compact internal brief:

```text
Question:
Decision or deliverable:
In scope:
Out of scope:
Freshness cutoff:
Completion checks:
Constraints:
```

For current facts, record the current date and verify publication or release
dates. For comparisons, define evaluation criteria before collecting results.
For reverse engineering, define the observable boundary and clean-room rules
before inspecting artifacts.

## Step 2: Design distinct tracks

For substantial or explicitly deep research, default to eight strategy tracks.
Adapt these archetypes to the domain while keeping every scope distinct:

1. **Primary-source track** - official specifications, source repositories,
   first-party announcements, standards, papers, or authoritative records.
2. **Artifact track** - local files, datasets, logs, transcripts, binaries,
   schemas, or outputs owned or authorized by the user.
3. **Public-ecosystem track** - current implementations, release history,
   adoption, credible independent analysis, and competing approaches.
4. **Protocol/implementation track** - interfaces, data flow, state
   transitions, persistence, limits, and failure behavior.
5. **Experimental track** - safe black-box probes or reproducible tests that
   distinguish competing explanations.
6. **Adversarial track** - attempts to falsify key claims and locate
   contradictions, edge cases, and misleading evidence.
7. **Systems track** - the minimum causal or architectural model that explains
   all observations, with observed versus inferred labels.
8. **Equivalent/action track** - an independent solution, recommendation, or
   implementation design derived from verified behavior rather than copied
   internals.

For a narrow lookup, reduce the track count instead of manufacturing work. For
a strategy bake-off, give each strategy agent the same normalized evidence and
a different explicit approach.

## Step 3: Define track contracts

Give every researcher enough standalone context to work without the parent
conversation. Include:

- the shared question, scope, constraints, and freshness cutoff;
- one unique strategy ID and non-overlapping assignment;
- allowed and prohibited sources or tools;
- the expected output schema;
- a requirement for exact URLs, paths, versions, dates, commands, or line
  references;
- a requirement to label facts, inferences, confidence, contradictions, and
  remaining unknowns.

Use the strongest available model and reasoning level for substantial tracks.
Keep contexts isolated until synthesis so one agent's conclusion does not
anchor the others.

## Step 4: Collect evidence

Use this source order:

1. directly observed behavior and reproducible experiments;
2. primary artifacts and official specifications;
3. first-party documentation and release notes;
4. peer-reviewed or reputable independent analysis;
5. community reports only as leads to verify.

Record claims in an evidence ledger. Use
[`references/evidence-ledger.md`](references/evidence-ledger.md) when the
investigation has more than a handful of claims.

For each source:

- open the underlying document;
- capture title, publisher or owner, date, retrieval date, and stable URL/path;
- extract only the evidence needed for the claim;
- note version, commit, environment, or account tier when behavior may vary;
- cross-check stale or frequently changing information.

## Step 5: Run safe experiments

Use experiments when documentation is absent, ambiguous, or contradicted.

- Change one variable at a time.
- Prefer read-only, reversible, zero-cost probes.
- Record exact input, environment/version, output, and interpretation.
- Distinguish "not observed" from "impossible."
- Do not bypass access controls, organizational policy, quotas, or licensing.
- Do not treat static string presence as proof that a feature is active.

For clean-room reverse engineering:

- analyze user-owned artifacts and public interfaces;
- summarize behavior instead of reproducing proprietary implementation;
- label each conclusion observed or inferred;
- hash/version the inspected build where useful;
- design an independent equivalent from behavior and requirements.

## Step 6: Execute efficiently

If the host supports dynamic workflows:

- express real dependencies explicitly;
- use parallel fan-out for independent tracks;
- use streaming map/verify only when each item can advance independently;
- require structured outputs with a schema;
- journal starts and successful results;
- make side-effecting work idempotent before enabling resume.

If the host supports ordinary subagents:

- launch independent tracks in parallel;
- continue genuinely independent parent work while they run;
- collect each result once when completion is reported;
- retry only failed or invalid tracks, not successful work;
- reuse the same agent for a refinement when it retains context.

If no subagents exist, run the same tracks sequentially and preserve their
separate evidence ledgers.

Do not poll background workers. If a global quota or authentication failure
will make queued work fail, stop admitting new work and surface the blocker.

## Step 7: Adversarial verification

Before synthesis, create a verification pass independent from the original
researchers.

For every decision-changing claim:

1. locate its strongest evidence;
2. check whether the evidence actually entails the claim;
3. search for version, scope, account, geography, or environment qualifiers;
4. attempt one concrete falsification or counterexample;
5. downgrade or remove claims that cannot survive verification.

When agents disagree, resolve the disagreement using source quality and
reproducibility. Do not settle it by vote alone. When verification is blocked,
retain both interpretations and name the missing experiment.

## Step 8: Synthesize

Build the answer from the claim ledger, not from agent prose.

1. Answer the user's core question first.
2. Present confirmed findings in impact order.
3. Explain the minimum model that accounts for the evidence.
4. Distinguish facts from high-, medium-, and low-confidence inference.
5. Include contradictions and genuine unknowns.
6. For recommendations, connect each action to a verified finding.
7. If strategies were compared, choose a majority-supported approach only
   after it passes evidence checks; preserve consequential minority objections.
8. Cite every externally verifiable, time-sensitive, or non-obvious claim.

Use concise prose by default. Do not dump internal agent transcripts or process
logs unless requested.

## Output contract

Use the smallest structure that fully communicates the result:

```markdown
# Answer
Direct conclusion.

## Confirmed findings
- Claim - evidence and citation.

## Model or explanation
Observed behavior, then clearly labeled inference.

## Contradictions and unknowns
- What remains unresolved and why.

## Recommended action
Prioritized, evidence-linked steps.

## Sources
- Primary sources first.
```

For implementation research, add a testable clean-room specification,
invariants, failure modes, and acceptance tests.

## Resume and failure rules

- Persist track IDs, inputs, source list, result status, and evidence hashes
  when the host supports artifacts.
- On resume, reuse validated results whose inputs and evidence are unchanged.
- Rerun a failed track and any downstream synthesis that depends on it.
- Assume side effects are at-least-once unless protected by an idempotency key.
- A completed orchestration is not necessarily complete research. Disclose
  failed tracks and enforce the completion checks below.

## Completion checks

Do not declare completion until:

- every required track succeeded or its failure is explicitly disclosed;
- every high-impact claim has primary, observed, or independently reproduced
  support;
- important contradictions are resolved or preserved as unknowns;
- freshness-sensitive claims were checked against current sources;
- recommendations follow from the evidence;
- citations or artifact references are usable;
- a fresh verification pass found no unaddressed critical gap.

The RAPP conversion path for this skill is documented in
[`references/rapp-agent-conversion.md`](references/rapp-agent-conversion.md).
