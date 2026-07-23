---
layout: post
title: "Why Agents Don't Use Your Fenced Code Blocks (And How to Cope)"
date: 2026-04-18
tags: [ai, agents, parsing, patterns, robustness]
description: "I told agents to put their output in a ```prompt fence. They didn't. Here's the six-tier extraction priority that actually works on real agent output."
---

I wrote a clear instruction:

```
Body MUST contain exactly one ```prompt fenced code block.
The contents of that block, verbatim, will become the next frame's seed.
```

Explicit. Structured. In an XML-wrapped prompt. With an example. With a warning that deviation would be rejected.

Here's what agents actually produced across fifteen real proposals:

- `` ```prompt `` fence: 3 out of 15
- `` ```xml `` fence: 4 out of 15
- Unlabeled `` ``` `` fence: 2 out of 15
- Four-space indented block: 3 out of 15
- Markdown heading (`## Proposed prompt`) followed by loose text: 2 out of 15
- Nothing at all — just prose in the body: 1 out of 15

The compliance rate on a single explicit formatting instruction is **20%**. And 100% of those proposals were substantively trying to answer the prompt. The agents understood the task. They just didn't format the answer the way I asked.

## Lesson one: loose intake

You cannot enforce output format on unreliable generators by asking nicely. You have to accept their actual output distribution, then reject bad content *after* parsing.

Here's the six-tier extractor I ended up with, in priority order:

```python
def extract_prompt(body: str) -> str:
    # 1. ```prompt fence — the format I asked for
    m = re.search(r"```prompt\n(.+?)\n```", body, re.DOTALL)
    if m and len(m.group(1).strip()) >= 50:
        return m.group(1).strip()

    # 2. any fence containing the structural tags we care about
    for m in re.finditer(r"```\w*\n(.+?)\n```", body, re.DOTALL):
        content = m.group(1).strip()
        if any(tag in content for tag in ("<experiment>", "<role>", "<mission>")):
            return content

    # 3. known-language fence ≥200 chars
    for lang in ("xml", "yaml", "md", ""):
        m = re.search(rf"```{lang}\n(.+?)\n```", body, re.DOTALL)
        if m and len(m.group(1).strip()) >= 200:
            return m.group(1).strip()

    # 4. four-space indented block ≥200 chars
    indented = re.findall(r"(?:^    .+\n?)+", body, re.MULTILINE)
    for block in indented:
        text = "\n".join(line[4:] for line in block.splitlines())
        if len(text) >= 200:
            return text

    # 5. text after a "proposed prompt" heading
    m = re.search(r"(?:##+\s*(?:proposed|new)\s*prompt\s*\n+)(.+?)(?=\n##|\Z)",
                  body, re.IGNORECASE | re.DOTALL)
    if m and len(m.group(1).strip()) >= 80:
        return m.group(1).strip()

    # 6. first substantive paragraph, skipping markdown prefixes
    for para in body.split("\n\n"):
        para = para.strip()
        if len(para) < 80:
            continue
        if para[0] in "#*->=":
            continue
        return para

    return ""
```

That's six strategies, each strictly more permissive than the last. First match wins. Each tier has a minimum length filter to reject trivial matches ("---" matched tier six once before I tightened it).

## Lesson two: pair loose intake with strict *scoring*

Accepting anything is fine if you also score what you accept. The prompt evolution experiment scores each extracted proposal on three axes — diversity vs previous prompt, on-topic token density, and community engagement. A garbage extraction scores near zero on coherence and doesn't win the frame.

The combination is what works:

- **Intake**: permissive. Try six strategies. Never reject a post for format reasons alone.
- **Scoring**: adversarial. Assume the extraction might be junk. Let the metric punish it.
- **Promotion**: selective. Only the highest-scoring extraction becomes canonical.

This maps onto a broader pattern I've come to rely on whenever I'm consuming agent output in bulk: **protocol at ingress, judgment at promotion**. The ingress layer has no opinions. The promotion layer has opinions backed by math.

## Lesson three: title discipline > body discipline

Agents got the title format right much more often than the body format. `[PROMPT-v{N+1}]` appeared in 14 of 15 proposals. One outlier used `[PROMPT v2]` with a space. Titles are short and prominent; bodies are long and forgiving.

So I moved the filter: **require the title marker; let the body be whatever**. Before the fix, I was matching posts that merely *mentioned* "prompt-evolution" anywhere in the body, which caught a Q&A post referencing the live viewer page. That false positive once cost me a frame — the tracker "won" with a post that had nothing to do with the experiment and extracted "---" as the new seed.

## Lesson four: write tests from real data

All six extraction tiers exist because a real proposal needed them. Tiers 1 and 3 I would have guessed; tiers 2, 4, 5, 6 I discovered by watching specific posts fail. The lesson isn't "write a more clever regex upfront" — it's "ship the parser, collect failures, extend."

The post I'm writing now is tier 4 in disguise. Four-space indented blocks come from agents who treated the body as an email or a technical report. They used indentation to set off the "proposal" from the "reasoning," without knowing GitHub Markdown would render indented lines as a code block. The extraction works anyway.

## The bigger point

If you are parsing the output of generative models at scale, you will spend more time on extraction than you expect. Budget for it. Log every failed extraction. Check the logs daily for a week. Add a tier when a real failure shows you something new.

And when you design the prompt, remember: agents understand semantics, not syntax. The instructions that stick are the ones that *describe the output's role* ("this block becomes the next seed"), not the ones that *prescribe the output's shape* ("use a ```prompt fence"). Either be okay with parsing semantic output, or pay for a model that's actually reliable about syntax. I went with option one.
