---
name: wow
description: Generate demo prompts that show off the current product's power — with a persistent ledger so suggestions never repeat and ambition ratchets up. Use whenever the user asks for "the coolest prompts", "mind-blowing prompts", "prompts that show off the power", "demo prompts", "give me 10", or is prepping a demo/pitch and wants material. Also use when the user reacts with "those are not that impressive" — that is ledger feedback, not a new request.
---

# Wow: demo-prompt generator with a memory

Kody fires "give me the coolest, most mind-blowing prompts" 20+ times a month, mostly in brainstem/RAPP repos, and the #1 failure mode is recycled or vague suggestions ("those are not that impressive"). This skill fixes that with a ledger and a concreteness bar.

## The ledger: `~/.claude/wow-ledger.md`

One table, append-only. Columns: `date | project | prompt (one line) | status`.
Status values: `suggested`, `used`, `landed` (Kody said it worked/demo went well), `flopped` (Kody said not impressive / it failed live).

- **Read it FIRST, every invocation.** If it doesn't exist, create it with the header row.
- **Never suggest anything semantically close to a prior entry for the same project.** Different wording ≠ new idea.
- If the user's message is a dissatisfaction reaction ("not that impressive", "more impressive than that"), mark the most recent `suggested` batch for this project as `flopped` before generating — flopped entries define the floor the new batch must clear.
- After presenting, append the new batch as `suggested`.

## Generating the batch

1. **Ground in the actual product.** Read enough of the current repo (README, agents/ directory, recent commits) to know what it can really do TODAY. Every prompt must exercise a real, currently-working capability — a demo prompt that errors in front of an audience is worse than a boring one (this has happened; see "you broke it in front of an exec").
2. **Concrete beats cosmic.** "Autonomously evolve this product for 24 hours" is a category Kody already uses. The bar for a wow prompt:
   - Runnable verbatim — a specific instruction, not a theme.
   - Visible payoff in under ~3 minutes — something appears on screen (a page, an agent responding, a live URL, a twin answering).
   - A "wait, it can do THAT?" mechanic — crosses a boundary the audience assumes is hard: touches their real data, produces a working artifact not a description, chains two systems (brainstem→Copilot Studio, transcript→deployed agent, vault→twin), or closes a loop live (build → ship → open the live URL).
3. **Escalate.** Order the 10 from "safe opener" to "closer". The last 2 should be the risky spectacular ones, flagged as such.
4. **Audience knob.** If context says exec/customer/VC, bias toward business-outcome framing (agent solves a named pain in their world); if peer/technical, bias toward architectural flex (P2P twin sync, self-modifying agents, RAR install-on-demand).

## Output format

Numbered 1–10. Each entry: the prompt itself in a code block (copy-paste ready), then ONE sentence on what the audience sees happen. No preamble essays. End with a one-line note of which 2 are the high-risk closers.

## Don'ts

- Don't re-serve a flopped idea with new adjectives.
- Don't suggest prompts requiring services that can fail live (fresh auth flows, rate-limited APIs) without flagging the risk.
- Don't pad — if only 7 clear the bar, deliver 7 and say why.
