---
layout: post
title: "Field Notes Are the Actual Moat"
date: 2026-04-18
tags: [field-notes, knowledge, moats, documentation, meta]
---

The thing that compounds in a long-running build is not the code. The code is replaceable. Better languages, better libraries, better paradigms come along, and rewrites happen. The interfaces survive. The implementations turn over.

What does not get replaced is the *field notes*. The accumulated record of what was tried, what worked, what didn't, why a particular pattern emerged, what the alternatives were, what made the alternatives wrong. The notes are the ledger of decisions. Every decision in a long-running system has a justification, and that justification was hard-won, and writing it down is the only way to keep it from evaporating.

Most projects do not write field notes. They write commit messages — too short. They write design docs at the start — too early. They write postmortems for outages — too narrow. They write blog posts when something ships — too polished. None of these are field notes.

Field notes are the running log of a builder's attention. They are written contemporaneously, in plain prose, addressed to a future self or a future colleague, with the casual specificity of a lab notebook. They name the actual tools used, the actual error messages encountered, the actual paths attempted. They explain what wasn't obvious. They preserve the texture of the decision.

The argument for field notes as a moat:

**They embody irreversible learning.** An anti-pattern discovered in week 12 of a project is a fact about the universe. Anyone can rediscover it, but rediscovering takes weeks. Reading the field note takes a minute. Field notes convert weeks of trial-and-error into minutes of reading.

**They survive personnel change.** Code reviews are conversations. They live in the heads of the participants. When the participants leave, the conversations are gone. Field notes are the conversations crystallized. New people can read them and absorb the shared context that the team built up.

**They are illegible to competitors.** A competitor can copy your code. They cannot copy your field notes, because they don't have them, and writing equivalent field notes requires running the equivalent experiments. The depth of the notes is a measure of the depth of the experience.

**They are illegible to attackers.** An attacker who exfiltrates your repo gets your code. They don't get the explanations of *why* your code is the way it is. The why is in the notes, and the notes are usually scattered across personal directories, build journals, post-mortems, and the team chat. The defender's understanding of the system exceeds the attacker's even when the code is identical.

**They turn into content.** A blog post that takes thirty minutes to write because the field notes already exist is essentially free. A blog post that requires generating the insight from scratch takes hours and risks being shallow. Field notes are the input to thought leadership; without them, thought leadership is performative.

The discipline is small. Pick a place — a markdown file in the repo, a folder of HTML pages on your site, a personal wiki. Give it a date stamp. After every session of meaningful work, spend ten minutes writing what you actually did and why. Not what the commit message says. The unstructured truth: what surprised you, what was harder than expected, what shortcut paid off, what shortcut backfired.

A specific format that's working for me right now: a folder of dated HTML pages, one per workstream session, each describing what was built that day, what was learned, what the live URLs are, and what the next steps would be. They're called *field notes*. They are linked from a small index page. They are written in plain prose. They are not meant to be polished. They are meant to be read in five years and still make sense.

The moat is not the code. The moat is the notes.
