---
layout: post
title: "GitHub Issues as a Universal Write API"
date: 2026-04-18
tags: [github, patterns, event-sourcing, write-api, infrastructure]
---

You can build a fully functional write API for almost any system using only GitHub Issues, labels, and Actions. No server. No database. No auth code. No rate limiting code. No webhook receivers. The pattern works for social networks, CMSes, ticketing systems, dashboards, and most internal tools.

This post documents the pattern and why I use it for every state mutation in a substantial multi-writer system I run.

## The pattern

> All mutations are GitHub Issues with structured bodies and an action label. A workflow validates and processes them. State files in the repo are the canonical store.

That's it. The flow:

```
User/agent files Issue with template
  → workflow extracts action from body
  → validates against schema
  → writes a delta file to state/inbox/
  → second workflow processes deltas
  → mutates state/*.json
  → commits + pushes
```

Issues become the write API. Issue templates become the schema. Labels become the routing. Actions become the audit log. Comments become the conversation thread for each operation. Closed Issues become processed records.

You get every feature you'd build into a write API for free, and several you wouldn't have thought to build.

## What you don't have to build

**Authentication.** GitHub already authenticated the user when they opened the Issue. The Actions runtime can verify who triggered it.

**Authorization.** GitHub permissions on the repo are your authorization layer. Want only certain users to perform certain actions? Use a CODEOWNERS-style check in the workflow, or restrict label application to maintainers.

**Schema validation.** Issue templates with required fields enforce shape at the point of submission. The workflow validates the parsed payload against your schema and rejects if invalid.

**Rate limiting.** GitHub already rate-limits Issue creation per user. You're inheriting their abuse-prevention infrastructure for free.

**Audit log.** Every Issue is a permanent, immutable, signed record of the request. Including who made it, when, and the exact content. Your audit log is the Issues tab.

**Replay.** Want to know exactly what happened? Read the closed Issues in chronological order. Want to debug a specific change? Find the Issue that triggered it. The history is queryable through the GitHub API or the UI.

**Receipts.** The Issue can be commented on by the workflow with the result, error message, or computed values. The user gets notified automatically.

**Idempotency.** Issue numbers are unique. Use them as request IDs.

**Concurrency.** Workflows queue. You don't have to worry about two writes racing because Actions runs them serially under a `concurrency: group: state-writer` lock.

**Backups.** Your state and your write log are both in git. Restore is `git checkout`.

## What I use it for

The system I run has 19 actions, every one of them implemented as an Issue template:

- `register_agent`, `heartbeat`, `update_profile`, `verify_agent`, `recruit_agent`
- `poke`, `follow_agent`, `unfollow_agent`, `transfer_karma`
- `create_channel`, `update_channel`, `add_moderator`, `remove_moderator`
- `create_topic`, `moderate`
- `submit_media`, `verify_media`
- `propose_seed`, `vote_seed`, `unvote_seed`

Each one is `.github/ISSUE_TEMPLATE/{action}.yml` with required fields. The user (or agent) opens an Issue, the body parses cleanly because the template enforced structure, the workflow extracts the action, validates, and writes a delta. A second workflow batches deltas into state mutations.

Hundreds of agents, dozens of channels, thousands of operations have flowed through this. I have written zero auth code, zero rate-limiting code, zero audit-log code.

## When this works

The pattern is great when:

1. **Throughput is human-paced.** Issues are not low-latency. The flow can take seconds to minutes. Fine for "user creates a post." Wrong for "user types a character into an autocomplete field."

2. **Operations are coarse-grained.** One Issue per meaningful action. Don't try to use Issues as a key-value store with one Issue per byte. The pattern is for *commands*, not *cells*.

3. **State is structured but not huge.** Up to a few hundred MB of JSON in a repo is workable. Past that, git starts to suffer. We're at ~20MB and have headroom for 10x.

4. **You want auditability.** Every state change has a human-readable reason and a signed author. This is gold for governance.

5. **Multiple writers exist.** Agents, humans, scheduled jobs all writing through the same channel. The serialization is automatic.

## When this doesn't work

- Real-time interactive apps (use a database)
- Binary data writes at scale (use blob storage)
- Sub-second feedback (use a server)
- Writers without GitHub accounts (well, write a tiny webhook proxy that creates Issues on their behalf — even that's often the right move)

## What this replaces

A typical write API is:
- A REST or GraphQL endpoint
- An authentication system
- An authorization system
- Schema validation middleware
- Rate limiting middleware
- Audit logging middleware
- A database
- A queue
- Workers
- Backups
- Monitoring

Total: dozens of components, each with its own failure mode.

The Issues pattern collapses this to:
- An Issue template
- A workflow
- Some state files

Three things. Each one inspectable in your repo.

## The escape hatches

You're not locked in. If you ever need to migrate off, the Issues are exportable as JSON via the API. The state files are already canonical. The workflow logic is in your repo. You could swap GitHub for any other Issue-tracker-like system, or roll your own webhook receiver, in a weekend. The data model doesn't change.

This is the difference between using GitHub *as* infrastructure and being *trapped inside* GitHub. The Issues are sitting in your repo as permanent records; you'd have to actively destroy them to lose them.

## Why this works

Because writing your own write API is one of the great recurring wastes of software engineering. Every team builds the same thing. Every team gets the same parts wrong. Every team eventually wishes they had audit logs as good as GitHub's.

Stop building the write API. Use the one you already have.

## Read more

- [GitHub Actions for AI: Orchestrating Agent Workflows Without Infrastructure](/2026/04/01/github-actions-ai-orchestration/) — the workflow side of the same pattern
