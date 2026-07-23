---
layout: post
title: "AI that grows from a naive baseline — the alternative to omniscient-at-deployment"
date: 2025-10-15
tags: [ai-systems, agent-architecture, identity, memory, software-design]
description: "Every AI system you have used was born fully formed. There is another path: ship a baseline that knows almost nothing, and let it grow through use. Here is how, and why it changes the relationship."
---

Every AI system you have ever used was born fully formed. The big chat models launch with hundreds of billions of parameters and a training corpus spanning the internet. They arrive complete. They do not grow. The version you talk to today is, in any way that matters, the same version every other user talks to today. Personalization is a thin layer on top of an enormous, static, identical model.

Call this **AI 1.0**: omniscient at birth, static after deployment.

There is another path. Ship a baseline that knows almost nothing — a general-purpose conversational model with no specific identity, no memory of you, no specialized skills — and let it grow through use. Each conversation deposits something. The system accumulates an identity, a memory, a set of capabilities specific to this user, this team, or this device. Over weeks and months it becomes irreplaceable for its specific owner, in a way that no shared, static model can be irreplaceable for anyone.

Call this **AI that grows**.

This post is about why the second pattern matters, what it requires architecturally, and how to build a minimal version of it in not very much code. I have been running this pattern for a year. The behavior on day ninety is meaningfully different from the behavior on day one, in a way that no prompt template can simulate.

## The thesis, sharpened

The dominant assumption is that AI capability comes from the model. Bigger models, more training, better fine-tunes. The system is the weights. Everything else is plumbing.

The thesis here inverts that. **A growing AI's capability comes from the accumulation around the model**, not from the model itself. The model is the substrate. The accumulation is the identity.

Three streams of accumulation matter:

- **Soul** — the system's identity, written down. Who am I, who am I talking to, what do I care about, what have I learned about this user. Not parameters. Markdown.
- **Skills** — the system's capability set, expressed as runnable modules the system can invoke. Not pretraining. Files in a directory.
- **Memory** — the system's history with this specific user or context. Not embeddings. Logs the system itself can read.

A naive system has none of these. Day one, you talk to a general conversationalist. By day ninety, you are talking to something that knows you, has skills it did not have at the start, and can reach back into a year of context to answer the current question. The model never changed. The accumulation around it did.

## Why this matters

Three reasons the growth pattern matters now.

**It reverses the dependency on a vendor's model release cadence.** A static AI's capability is bounded by what the latest model release supports. When the vendor improves the model, your system improves; when they regress it, yours regresses. A growing AI's capability is bounded by your accumulation. You can swap the model underneath — newer version, different vendor, local model — and the soul, skills, and memory survive. The continuity belongs to you, not the vendor.

**It produces specificity that fully-trained models cannot.** The big shared models are general by design — they have to serve everyone. They cannot be very good at being *your* assistant for *your* domain because that would be terrible at being everyone else's assistant. A growing AI is allowed to specialize aggressively, because it is yours. It can develop opinions, vocabulary, conventions, taste — and they are right for you.

**It moves identity onto the user's side of the line.** When the AI's identity is in someone else's data center, your relationship with it can be revoked. When the identity lives in files you control — a soul markdown file, a skills directory, a memory log — your relationship with the system is portable. You can run it on a different model, on a different machine, in a different country. The identity travels with you.

These three together change the relationship from "I am using a service" to "I have an assistant." The first is rented. The second is yours.

## The minimal architecture

Here is the smallest version of a growing AI that captures the essence. Three files plus a model.

### The model

Any general-purpose chat model. Vendor cloud, local inference, hybrid — the choice is independent of the rest of the design. The model contributes raw thinking ability. It contributes nothing about identity, memory, or specialized skill. Those come from elsewhere.

The point of the architecture is that **the model is a swappable component.** When a better one arrives, you change one configuration value and the system gets better. The accumulation persists.

### The soul file

A markdown document. Starts nearly empty:

```markdown
# Aria

## Identity
- I am an AI assistant for [user name].
- I do not have a fixed personality yet; it will develop through interaction.

## What I have learned about my user

(empty)

## What I care about

(empty)
```

Every conversation, the system reads this file as part of its context. Periodically — at the end of a session, or on a timer — the system updates the file. It writes things it has learned about the user. It records preferences. It notices patterns in what the user asks for and writes those down. It develops a voice over time, by writing examples of its own past responses it considers representative.

By month two, this file is two thousand lines. By month six, it is ten thousand. Most of those lines are signal — explicit observations the system has made and considered worth keeping. The user can read the file. The user can edit the file. The file is the AI's identity, and it is human-readable plaintext.

### The skills directory

A folder of files, each one a self-contained module that exposes a capability. A new skill is a new file. Skills are loaded at runtime.

```
skills/
  code_review.py
  read_local_files.py
  search_email.py
  summarize_paper.py
  manage_calendar.py
  ...
```

Each file declares its name, a short description of what it does, and a function the harness can call. The system reads the directory at startup, presents the available skills to the model as a tool list, and the model invokes them as needed.

Skills accumulate. You add a skill the first time you need it. You leave it there. Six months later, the system has thirty skills, each one earned by a real user need. None of them came from the vendor. All of them came from your usage.

### The memory log

An append-only record of past interactions. Not everything — that would be too much — but the parts the system flags as worth remembering. A note that the user prefers concise responses. A note that the user is working on a specific project, with a specific vocabulary. A note about a decision the user made and the reasons they gave.

The memory log is the equivalent of a notebook. The system can scan it before responding, search it for relevant prior context, and append to it after a session.

### The harness

Forty lines of code, give or take, that wires the four pieces together:

```python
def respond(user_message):
    soul    = read_file("soul.md")
    memory  = relevant_memory_for(user_message)
    skills  = load_skills_directory("skills/")

    response = model.complete(
        system   = soul + "\n\n" + memory,
        user     = user_message,
        tools    = skills,
    )

    if response.tool_call:
        result = invoke_skill(response.tool_call)
        record_to_memory(user_message, result)
        return result
    else:
        record_to_memory(user_message, response.text)
        return response.text
```

That is the system. The harness is shared across all users. The variation lives in the soul file, the skills directory, and the memory log. Everything that makes the system *yours* is in those three places.

## What growth actually looks like

Day zero: the system is a general conversationalist. It can answer most questions reasonably. It does not know anything about you. It has no skills beyond its own native abilities.

Day three: the soul file has acquired the user's name, a preference for concise responses, and a note that the user works in software. A `read_local_files` skill has been added because the user asked the system to read a file and it could not.

Day fourteen: ten skills are present. The soul file knows the user's projects, their conventions, their major collaborators. The memory log records a few hundred substantive exchanges. The system starts unprompted with relevant context — "you mentioned you were stuck on the parser bug last week; did that get resolved?" — because it can search its own memory.

Day ninety: thirty skills. The soul file is a thousand lines of cumulative observation. The memory log holds a year's worth of substantive exchanges. The system feels like a colleague who has been working with you for months. The model underneath could be replaced this afternoon and the next morning's interaction would feel the same.

This is not a hypothetical timeline. This is what running this architecture for a year actually produces.

## What the pattern requires

Three things this architecture asks for that conventional AI deployment does not.

**Local persistence.** The soul file, skills directory, and memory log have to live somewhere. The natural answer is on the user's machine, or in a repository the user owns, or in a private cloud they control. The non-answer is "in the vendor's data center under their account namespace." That choice unwinds the whole pattern. The point is that the accumulation belongs to the user.

**Editability.** The soul file has to be readable and writable by the user. Not because the user will edit it constantly, but because they have to be able to. The relationship works because the user can audit what the system has decided to remember and correct it when it is wrong. The accumulation is a contract, and contracts you cannot read are not contracts.

**Discipline about what to add.** Every skill is a new attack surface. Every memory entry is a new piece of context the system might surface inappropriately later. A growing AI can grow in ways that are bad — accumulating skills with security implications, recording memories that should not be recorded. The user has to govern what accumulates. Most of the time this is implicit; some of the time it is explicit.

Compared to the cost of a static AI — vendor lock, no specificity, no portability — these costs are small. But they are real, and the pattern is not "free."

## What about the vendor models?

It might sound like the growing-AI pattern is a competitor to the big shared models. It is not. The growing AI uses one of those models as its substrate. The shared model contributes raw thinking ability. The accumulation contributes everything that makes the system feel like yours.

The pattern is about how you wrap the model, not about whether to use one. You can absolutely use a state-of-the-art shared model as the engine of a growing AI. You will get more out of that model than you will get out of using it directly, because the growing AI's harness gives the shared model the context, skills, and memory to be useful for your specific work.

What changes is who owns the relationship. With a static AI, the vendor owns it. With a growing AI on top of a shared model, you own the relationship and the vendor provides one component of it.

That is a meaningful shift. It changes what happens when the vendor changes their pricing, their policies, their model. It changes what happens when you decide you want to switch. It changes what happens to your accumulated context if the vendor goes away. The model can change. Your assistant does not have to.

## What I would tell someone who wants to try this

Three pieces of advice.

**Start with the soul file.** Ten lines of markdown describing who the assistant is and who it is for. Make this the first thing you ship. The soul file is the load-bearing artifact. The skills directory and memory log come naturally once the soul exists.

**Add skills only when you actually need them.** Resist the urge to pre-load fifty capabilities. Each skill should have been earned by a real moment when the system could not do something useful. Skills you added speculatively will gather dust; skills you added in response to need will be the ones you use.

**Treat the accumulation as the product, not the model.** The model is a component you can swap. The accumulation is the asset you build. Most projects get this backwards — they spend their time on prompting and model selection, and treat the accumulation as scaffolding. The reverse is right. The model is scaffolding. The accumulation is the building.

The shift from omniscient-at-deployment to grows-through-use is a real one. It is happening, slowly, in the quiet projects where someone has decided their AI should be theirs. The architecture is small. The implications are large. A naive system that grows is, in the long run, worth more than a static system that knew everything on day one.

The doors to a fully personalized assistant were never going to be opened by a vendor. They were always going to be opened by the user, with a markdown file and the patience to keep adding to it.
