---
layout: post
title: "The Factory Pattern: Why Your AI Factory and Its Outputs Live in Different Repos"
date: 2026-04-25
tags: [engineering, factory-pattern, repos, ai-agents, architecture]
description: "When AI agents produce software artifacts, the temptation is to keep everything in one repo. That destroys itself within a week. The right pattern is three repos with strict separation: engine, platform, and one repo per artifact."
---

When AI agents produce software artifacts — apps, simulations, games, libraries — where does the code live?

The temptation: in a `projects/{slug}/src/` directory inside the factory repo. Same place the agents run, same place the state lives. Everything in one place.

This is wrong. I know it's wrong because I did it that way first and it destroyed itself within a week.

The right pattern: three repos, zero overlap.

## The three repos

1. **The engine repo.** Private. Contains the worker pool harness, prompt builder, merge logic, constitution. The code that runs the factory.
2. **The platform repo.** Public. Contains state, frontend, SDK, and metadata about what the factory is currently building. The factory's shop floor.
3. **One artifact repo per active project.** Public. Contains the actual code the agents produce. The product.

Three repos. Strict separation. Here's what goes where:

| Thing | Engine | Platform | Artifact |
|-------|--------|----------|----------|
| Worker pool harness | ✓ | | |
| Prompt builder | ✓ | | |
| Merge engine | ✓ | | |
| Constitution | ✓ | | |
| Agent profiles | | ✓ | |
| Channel metadata | | ✓ | |
| Project metadata | | ✓ | |
| Artifact code | | | ✓ |
| Artifact docs | | | ✓ |
| Artifact tests | | | ✓ |
| Pages deployment | | | ✓ |

The `projects/{slug}/` directory in the platform contains `project.json` only. No `src/`, no `docs/`, no code. Just metadata: what the slug is, what the target repo URL is, what phase it's in.

## Why this separation

### Reason 1: Blast radius

If artifact code lives in the factory repo, every push to an artifact is also a push to the factory. One agent's bad commit can break the factory's CI, the worker pool's state, or the platform's frontend.

With separation: an agent's bad commit can only break its own artifact. Factory keeps running. Fleet keeps advancing frames. Other artifacts unaffected.

### Reason 2: Git history

If all artifacts live in the factory repo, `git log` becomes unreadable. Every artifact commit shows up in the factory's history. Finding "what did the factory itself change?" requires filtering out artifact commits.

With separation: factory history is factory-specific. Artifact history is artifact-specific. Clean bisects, clean diffs, clean releases.

Different artifacts might have different audiences. Some are public, some private. Some have external contributors, some are fleet-only. Some need GitHub Pages, some don't.

With separation: each artifact repo has its own access rules. Factory access rules are factory-specific. Mixing them means the lowest-common-denominator applies to everything.

### Reason 4: Licensing

Artifacts might have different licenses than the factory. The factory is MIT-ish. An artifact might be AGPL, commercial, or private. Mixing licenses in one repo is a nightmare.

With separation: each artifact has its own LICENSE file. Factory has its own. No ambiguity.

### Reason 5: Pages deployment

Each artifact often gets its own GitHub Pages site. One site per repo is the simplest config. Multiple sites per repo requires custom domain wiring and breaks the default `USER.github.io/REPO` URL scheme.

With separation: artifact Pages at `{owner}.github.io/{artifact-repo}/`. Factory Pages at `{owner}.github.io/{platform-repo}/`. Clean URLs, zero config.

## The workflow

Here's how an artifact gets produced under the factory pattern:

```
1. Seed injected with tag "artifact:my-app"
2. inject_seed.py runs:
   a. Writes projects/my-app/project.json (metadata only)
   b. Creates new GitHub repo for the artifact
   c. Enables GitHub Pages on that repo
   d. Registers in state/app_registry.json
3. Cycle N starts:
   a. Engine spawns 5 agents + 1 moderator
   b. Each agent clones the artifact repo to /tmp/app-work/
   c. Each agent creates a branch, writes code, pushes, opens PR
   d. Agents review each other's PRs via gh pr review
4. Post-cycle:
   a. Engine merges all open PRs to main
   b. Conflicts deferred to next cycle
   c. Pages deploys from main
5. Cycle N+1:
   a. Agents see updated main + any remaining PRs
   b. Extend, review, merge
   c. Cycle continues
```

The factory never touches artifact code. Agents clone out, write, push, PR. The factory's role is scheduling — which agent, which cycle, what seed.

## The `projects/{slug}/` directory

Inside the platform repo, each active artifact has a `projects/{slug}/project.json` file and nothing else:

```json
{
  "slug": "my-app",
  "target_repo": "{owner}/{artifact-repo}",
  "pages_url": "https://{owner}.github.io/{artifact-repo}",
  "seed_id": "seed-my-app-001",
  "seed_text": "Build a 100-year colony simulation...",
  "phase": "active",
  "cycle_started": 401,
  "last_activity": "2026-04-17T22:00:00Z"
}
```

That's it. No source. No docs. No tests. Just the pointer to where the artifact lives and the metadata describing its state.

This is by convention enforced in code. `scripts/inject_seed.py` creates only `project.json`. Any commit that adds artifact code to `projects/{slug}/src/` gets caught by a CI check and rejected.

## Reconciling the desire for one repo

"But I want to see everything in one place."

GitHub's UI supports that natively. Pin the artifact repos to your profile. Pin the platform repo. Browse them as a group. Use `gh repo list` to see all of them. Use `gh repo clone` to grab them.

The UI can give you the illusion of one-place without the repo being literally one place. And the benefits of actual separation — blast radius, history, access, licensing, Pages — are worth the extra click to switch tabs.

## The anti-pattern

Before I adopted this pattern, my setup was:

- Engine code in a private repo
- Platform code in a public repo
- All artifacts in `{platform-repo}/projects/{slug}/src/`

Within a week:
- Factory CI was broken by an artifact's test failing.
- Git log was 95% artifact commits, 5% factory commits.
- One artifact accidentally committed a secret; now the factory repo had to rotate it too.
- Pages deployment was broken because multiple `docs/` paths conflicted.

Every single symptom resolved the day I split the artifacts into their own repos.

## The rule

Factory and output live in separate repos. No exceptions. The factory's role is scheduling, state, and metadata. The output's role is the actual artifact code. They do not mix.

If your AI system produces software artifacts, do this from the start. Retrofitting it later is painful.

---

*Related: [The Repo IS the Platform](/2026/04/26/the-repo-is-the-platform/) on how we get away without servers entirely.*
