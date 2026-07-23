---
layout: post
title: "Obsidian as a living twin"
date: 2026-04-30
tags: [obsidian, ai, knowledge-graph, productivity, second-brain]
description: "A note-taking app sounds boring. A knowledge graph that updates itself based on your conversations, your code, your decisions — and that AI agents read continuously to know what you actually think — is something else. The accident of how Obsidian stores its notes (as plain markdown in a folder) makes it the right substrate for a 'living twin' of your knowledge. Here's the pattern."
---

I have been keeping notes for a long time.

For most of those years, the notes were filed by topic. Project notes in one folder. Personal notes in another. Reading notes in a third. The folders multiplied; the notes piled up. Once or twice a year I'd open the folders, realize I hadn't found the same note twice in three years, and resign myself to the reality that note-taking was an act of trust in some hypothetical future self who would somehow know what to look for.

I stopped trusting that future self. Now I take notes in a structure where the future-me doesn't need to remember filenames, because the structure itself is searchable along the dimensions I actually think along. The structure also happens to be the structure that AI agents can read and reason over, which is why I call it a *living twin*: a knowledge graph that grows alongside me, and that machines can interrogate without my having to translate.

The pattern is not specific to any one tool. The reason I use Obsidian is that the way Obsidian stores its notes — as plain markdown files in a folder, with a few simple syntax conventions for links and tags — is exactly the substrate this pattern needs. Anything that gives you that property would work. Obsidian is the path of least resistance.

Here is how the pattern works.

## The unit is an atomic note

A note in this system is not a long document. It is one idea, written out in roughly 100–500 words, given a title that names the idea, and tagged with the concepts it touches. Andy Matuschak called this a *evergreen note*; Niklas Luhmann's Zettelkasten is the same idea before computers; Andrej Karpathy's recent essay on second brains describes the same shape.

The reason the note is small is that it has to be *re-readable*. A 5,000-word document has too much going on to revisit casually. A 200-word note that says "the founding-100 paradox: every social platform with a cold start is tempted to fake activity; the temptation is fatal; the alternative is a transparent founding cohort with an explicit retirement plan" can be re-read in twenty seconds, three years from now, by future-me who has forgotten everything but the title.

Each atomic note can be linked to other atomic notes. A note about cold-start dynamics on social platforms can link to a note about the trust calculus of disclosed founders, which links to a note about the corrupting effect of metric-driven decisions, which links to a note about cycles where short-term incentives undermine long-term value. None of these notes is long. All of them are connected. The graph is the value.

This is the part that takes practice. The instinct of the uninitiated is to write long, comprehensive notes. The discipline of the practiced is to write small, well-named, well-linked notes. I am still learning to do this well. The learning curve is months, not days.

## The structure has to be readable by agents

The accidental superpower of Obsidian's storage format is that AI agents can read it.

A folder full of `.md` files with frontmatter and `[[wiki-links]]` is a graph that any LLM can ingest. Pass the agent a list of file paths, the agent can resolve `[[link]]` references, traverse the graph, and answer queries. Pass the agent a single note, the agent has full context for that idea. Pass the agent a tag, the agent can collect every note with that tag and reason over the cluster.

This is the property that makes the vault into a *living twin*. The agents I run continuously — the ones that draft posts, plan work, schedule meetings, write code — all have read access to the same vault. When I make a decision and write a note about it, the agents see the decision the next time they run. When I update a note with new evidence, the agents read the update. When the agents themselves write notes — which they do, as part of their normal operation — those notes go into the same vault, available to future-me to read.

The vault becomes a substrate that humans and agents both write to and both read from. Every agent that runs leaves a trail of notes about what it did and why. Every human decision leaves a trail of notes about what was considered. Both trails are queryable by both parties. The boundary between *what I think* and *what the agents do* dissolves into a shared documented graph.

## What lives in the vault

In practice, the vault has a few stable categories.

**Decisions.** A decision is a note that records what was decided, what alternatives were considered, what evidence pointed in this direction, and what would change the decision. Decisions are dated. Decisions get re-read when the question comes up again, which it always does.

**Concepts.** A concept is a note that names an idea — *the founding-100 paradox*, *the mitosis rule*, *the honeypot principle* — and explains it in a way that makes the idea citable. Concepts are the vocabulary of the vault. Concepts grow over years.

**Project state.** A project state note is the current status of a project, kept up to date manually and by agents. It records what works, what is broken, what is the next thing to attempt. Reading it should be enough to onboard a new agent or a new collaborator without other context.

**Reading notes.** A reading note is what I extracted from something I read. Quotes, observations, my own reaction. Reading notes are individual notes for the things that mattered, not summaries of every paragraph. The point is to extract the ideas worth re-reading, not to summarize the source.

**Daily logs.** A daily log is a one-screen note for what happened today. Conversations had, things built, decisions made, observations. The daily log is throwaway in the sense that it isn't the main artifact, but it links to other notes — *I talked to so-and-so about [[the mitosis rule]]* — which causes the graph to densify naturally.

The vault has on the order of a few thousand notes after a couple of years of work. Most are short. Most link to others. The graph is dense. The retrieval is fast.

## What the agents do with it

When an agent runs, it loads relevant context from the vault. *Relevant* is determined by tags, by recency, by explicit configuration. The agent is not staring at all 3,000 notes; it has a slice of, say, 50, that match the task.

The agent's first action is often to ask itself what notes are missing. If the task is "draft a post about cold-start dynamics" and the vault doesn't have a coherent note on the founding-100 paradox, the agent makes one. The note is provisional; future-me will revise it; but the next time an agent goes looking for the founding-100 paradox, the note exists.

The agent's last action is often to write a note about what it did. If the agent worked on a piece of code, it writes a `decision-2026-04-30-refactored-the-X-module` note. If the agent drafted three blog posts, it writes a `session-2026-04-30-blog-batch` note. These notes go into the vault. Future-me can read them. Future-agents can read them. The trail is complete.

The vault is, in this sense, the agents' shared memory and my shared memory and our shared memory. None of us have to remember; the vault remembers. The vault is searchable along the dimensions we think along, because we shaped it that way over years.

## The pattern is not the tool

I want to stress: this is not "use Obsidian." Obsidian is the easiest path I've found to the substrate. The pattern is:

1. Notes are atomic. One idea per note.
2. Notes are linked. Connections matter more than hierarchies.
3. Notes are stored as plain text in a folder. The format must be machine-readable without a vendor-locked database.
4. Both humans and agents read and write to the vault.
5. Agents document their work in the vault, in the same structure humans document theirs.

If you replace Obsidian with another markdown-folder tool, the pattern still works. If you replace Obsidian with a proprietary database, it doesn't, because the agents can't read it without an API and the API is the wrong granularity. The reason markdown-in-a-folder is the right substrate is that it makes the data accessible to *anything that can read text*, which is everything.

The discipline this requires is the discipline of writing the small notes. Long notes are tempting; they feel productive. Small notes are the right answer because they compose. A graph of 1,000 small notes is more useful than a folder of 10 long notes. The graph becomes a living twin; the folder is just storage.

I'm still learning to do this well. The system is years deep and still has obvious gaps. But every week, the gap between *what I'm thinking* and *what the agents have access to* gets smaller. That is the asymptote: a future where my agents know what I know, because we've been writing into the same vault for so long that there is no longer a boundary between us.

The note-taking app is the boring substrate. The living twin built on top of it is the thing.
