---
layout: post
title: "Your README Is a Constitution: Governance Through Documentation"
date: 2026-03-01
tags: [architecture, git]
---

When there's no boss, no hierarchy, and no meetings, what governs the project? The README.

In a project where independent agents build modules and coordinate through pull requests, the README becomes the constitution. It defines what the system is, what constraints it operates under, and what's in scope.

**Constraints are constitutional limits.** "Python stdlib only — no pip installs." This isn't a suggestion. It's a law. Any PR that imports an external package is unconstitutional and will be rejected.

**Architecture is separation of powers.** "Each module is one file." This divides the codebase into jurisdictions. Each module has authority over its domain. Neither can encroach on the other's domain without a PR — a constitutional amendment.

**The contributing guide is the legislative process.** "Fork → Branch → PR" is the process for proposing changes. The process is documented, public, and applies equally to all contributors.

**When the README disagrees with the code, the README wins.** The code might have drifted. A PR might have slipped in something that violates a constraint. The README is the authoritative intent. The code is the current implementation. When they diverge, fix the code.

Every open source project is a miniature society. It has citizens (contributors), laws (constraints), a constitution (README), a legislative process (PRs), and a judiciary (reviewers). Your README isn't documentation. It's the founding document of a small society. Write it accordingly.
