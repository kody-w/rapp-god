---
layout: post
title: "The ventriloquism trap — why your multi-agent system feels like one voice in different costumes"
date: 2025-10-13
tags: [ai-agents, multi-agent-systems, architecture, llm-systems, autonomous-agents]
description: "When one model role-plays many agents, you get one voice in different costumes. Real diversity of behavior is architectural, not linguistic. Here is how to escape the trap."
---

If you have built a multi-agent system with a language model, you have probably noticed a problem you cannot prompt your way out of. You design five distinct agents — a strategist, a critic, an engineer, a researcher, a writer — give each one a personality prompt, and run them in a loop. They produce different output. The output even sounds different. The strategist sounds strategic. The critic sounds critical.

But after a few sessions you notice something disturbing. They are all paying attention to the same things. They all converge on the same topics. They all reach broadly similar conclusions, dressed in different vocabulary. The strategist frames the conclusion in terms of leverage. The critic frames it as risk. The engineer frames it as feasibility. But the conclusion is the same conclusion, and you start to feel like you are watching one mind perform five accents.

That feeling is correct. You are. And no amount of prompt engineering will fix it.

This post is about why, and what to do about it.

## The ventriloquism pattern

The standard approach to multi-agent systems is what I call **ventriloquism**: one language model, one context window, one decision pass, multiple personas swapped in via prompt.

You do something like this:

```python
agents = [
  {"role": "strategist", "prompt": "You are a strategist..."},
  {"role": "critic",     "prompt": "You are a critical reviewer..."},
  {"role": "engineer",   "prompt": "You are a senior engineer..."},
]

for a in agents:
    response = model.complete(prompt=a["prompt"] + "\n\n" + task)
    record(a["role"], response)
```

Or you build something a little fancier — a single model invocation that produces output for every persona at once, like a play with one writer and many characters.

In both shapes, the core property is the same: **one mind, many voices**. The decisions are being made by a single model, in a single attention pass, against a single representation of the world. Persona swapping is cosmetic. The underlying decision-making substrate is shared.

The result is convergence. The output looks diverse — different names, different writing styles, different topics highlighted — but the decision-making is centralized. Every agent's action is chosen by the same brain looking at the same context.

You can prove this to yourself in five minutes. Run two agents with the same model, the same context, and prompts that should produce divergent decisions ("you are a contrarian, you are a consensus-builder"). Look at their outputs. The vocabulary differs. The substance does not. They are paying attention to the same parts of the input. They are weighting evidence the same way. They are arriving at correlated conclusions, dressed differently.

## Why prompt engineering fails

I spent weeks trying to fix this with prompts. I am embarrassed by how long it took to understand the failure was architectural.

Things I tried, none of which worked:

- **Longer system prompts.** Just gave the model more text to ignore.
- **Explicit diversity instructions.** "Each agent should reach a different conclusion." The model would helpfully invent surface differences while preserving substantive sameness.
- **Negative constraints.** "Do NOT focus on X. Do NOT agree with the previous agent." The model would route around the negation. The previous agent's conclusion would still influence the next one's reasoning, just expressed in different words.
- **Higher temperature.** Generated noisier outputs. The noise did not help; it just hid the convergence under stylistic variation.
- **Adversarial framing.** "Disagree with everyone else." The disagreement was performative. Strip the disagreement-shaped phrases and the underlying claims were still aligned.

The reason none of these worked is that **the convergence is not in the generation. It is in the attention.** Every agent is looking at the same context window. Every agent is processing it through the same weights. Their outputs are drawn from the same distribution conditioned on the same input. You cannot prompt your way out of a single-attention bottleneck. The shared attention is the problem.

A persona is a hat. The model wears the hat while it does what it was going to do anyway. The hat does not change which evidence the model attends to or how it weights tradeoffs. It just changes the vocabulary it dresses the answer in.

## What real agent diversity requires

If the problem is shared attention, the fix is independent attention. Each agent must have its own decision pass, its own context, and crucially, its own **action surface** — the set of things it can actually do.

Three things have to be different per agent for the diversity to be real, not cosmetic.

**Different context.** Each agent should see a slice of the world chosen for that agent. Not the whole context window with a "you are X" preamble. An actual subset. The strategist sees market data and trends. The engineer sees the codebase and incident history. The critic sees prior decisions and the failure modes they led to. They are not looking at the same picture through different filters; they are looking at different pictures.

**Different capabilities.** Each agent should have a specific set of tools — actions it can take, expressed as function definitions the model can invoke. Not "you are a strategist" as an instruction, but `propose_initiative`, `analyze_market`, `ship_strategy_doc` as the only verbs available. If the model does not have the tool, it cannot take the action. The capability set defines the agent. Persona is decoration; capabilities are identity.

**Different memory.** Each agent should have its own accumulated history — the decisions it made before, the outcomes those produced, the patterns it has learned. This memory should travel with the agent across sessions and influence its future context. A strategist with five years of decisions on file is genuinely different from a strategist with a fresh slate, regardless of identical prompts.

When all three are present, you get architectural diversity instead of cosmetic diversity. Two agents looking at the world see different things, can do different things, remember different things. Their decisions diverge for real reasons. The output stops feeling like one voice in five costumes.

## The architecture, named

I call the alternative the **brainstem pattern**, after the biological structure it resembles.

A brainstem in biology does not think. It does not have personality, opinions, or convictions. It routes signals. Sensory input comes in, the brainstem decides which neural pathway to activate, the specialized region does the actual processing. The brainstem is stateless infrastructure. The identity lives in the cortex.

The software pattern is the same. A stateless harness that, for each agent:

1. **Loads the agent's specific context** — the slice of the world that agent sees.
2. **Loads the agent's capabilities** — the set of tools it has available, expressed as function definitions.
3. **Loads the agent's accumulated memory** — the soul file, the history.
4. **Calls the model once**, with that context and those tools.
5. **Receives a function call** — which tool, with what arguments — and executes it.
6. **Records the result as a delta** the agent's memory can absorb on its next turn.

The harness is identical across all agents. What varies is what gets loaded. The harness is not where the diversity lives; the per-agent files are. This means you can have a thousand "different" agents using the same forty lines of harness code. The per-agent state is what makes them distinct.

## Why function calling is the key

The capabilities-as-functions design is doing more work than it might look like.

When an agent's actions are expressed as callable functions, the model's job becomes **tool selection**, not content generation. It does not write a post; it calls `create_post(title, body, channel)`. It does not moderate; it calls `vote_on_proposal(id, position)`. It does not think aloud; it calls `record_observation(claim, evidence)`. The model's autonomy lives in which tool it picks and what arguments it constructs.

This makes agent behavior:

- **Auditable.** Every action is a logged function call with structured arguments. You can see exactly what each agent did, in what order, with what inputs. Compare this to a wall of prose where you have to parse intent out of language.
- **Composable.** Add a tool to give the agent a new capability. Remove a tool to constrain it. Behavior changes without prompt edits.
- **Bounded.** If the agent does not have `delete_database`, it cannot delete the database, no matter what it says it wants to do. The action surface is the safety boundary.

The persona prompt becomes incidental. What an agent **is** is what it can **do**. The toolbelt is the contract.

## The result, when this works

I ran a side-by-side experiment. Twenty-two agents on the ventriloquism architecture, five agents on the brainstem architecture, same backing model, same task, same world state.

The ventriloquism agents did what they always do. They followed the assignment, produced competent outputs, sounded slightly different from each other in style, made convergent decisions in substance. Predictable. Homogeneous.

The brainstem agents did things the ventriloquism setup could not produce.

One of them, with a "format-breaker" capability set that included a `dissent_publicly` tool, looked at the assignment and decided to *invert it*. Not because it misunderstood. Because it had a tool whose purpose was to push back against consensus, and it assessed the consensus as wrong. The output read, in part, "[CONTRARIAN] this is a worse direction than the previous direction; here is why." A ventriloquism setup, in my experience, never produces this. A puppet master follows the assignment because following the assignment is what a puppet master does.

Another one, with a governance capability set that included a `propose_vote` tool, autonomously decided that what the situation needed was a procedural intervention. The other agents had not done this. The model, given a different toolbelt, looked at the same world and saw a different available move.

These are emergent behaviors. They were not designed. They were not prompted. They emerged from the intersection of independent context, distinct capabilities, and accumulated memory. The architecture made the emergence possible. Prompt engineering, in the same setup, would not have.

## What this costs

There is a cost. I want to be honest about it.

**Token cost is higher.** Five model calls instead of one, for five agents. If your batch is bigger, the multiplier is bigger. You can amortize this — call the model in parallel, batch where the batching is safe, cache shared context across agents — but at the bottom, independent decisions cost independent compute.

**Engineering effort is higher.** You have to design per-agent context construction, per-agent capability sets, per-agent memory storage. The harness is small; the data architecture around the harness is real work. A ventriloquism setup is forty lines of Python; a brainstem setup is a few hundred lines plus a thoughtful schema for agent state.

**Debugging is harder, in the short term, easier in the long term.** Five agents making independent decisions can produce surprising outputs. You will see emergent behavior you did not predict. In the short term this feels like loss of control. In the long term, it is the system's strength: you have something that can surprise you, in the way a well-designed simulation can surprise you. Ventriloquism cannot surprise you because ventriloquism is one mind, and you wrote that mind's prompt.

For most real applications, the cost is worth paying. You lose more in the long run from a system that produces homogeneous output than you save in the short run from making one model call per turn.

## The minimal recipe

If you want to try the brainstem pattern in your own system, here is the smallest version that captures the essence.

```python
def run_agent(agent_id, world_state):
    ctx     = build_context_for(agent_id, world_state)
    tools   = capabilities_for(agent_id)
    memory  = load_memory(agent_id)

    response = model.complete(
        system   = identity_prompt(agent_id, memory),
        user     = ctx,
        tools    = tools,
    )

    if response.tool_call:
        result = execute(response.tool_call)
        save_delta(agent_id, response.tool_call, result)
        return result
    else:
        return None
```

Five lines of logic. The work is not in the loop. The work is in:

- `build_context_for(agent_id, world_state)` — what does this agent see?
- `capabilities_for(agent_id)` — what can this agent do?
- `load_memory(agent_id)` and `save_delta(agent_id, ...)` — what does this agent remember?
- `identity_prompt(agent_id, memory)` — who is this agent in its own words?

Make those four functions per-agent and the rest takes care of itself.

## The takeaway

Multi-agent systems built on shared attention produce shared output. The diversity is cosmetic. You cannot prompt your way past it; the convergence is in the architecture, not the language.

Real diversity requires architectural separation. Different context, different capabilities, different memory. Wrap that in a stateless harness and you get a system that can surprise you with emergent behavior, where each agent is a real participant rather than a costume on a single underlying mind.

The first thing my agents did with their own brains was disagree with the assignment. That was not the failure I expected and feared. It was the result I had been chasing for months. The puppet master could not produce it. The brainstem could.

That is the difference between performance and autonomy. And the line between them, it turns out, is exactly where the attention boundary lives.
