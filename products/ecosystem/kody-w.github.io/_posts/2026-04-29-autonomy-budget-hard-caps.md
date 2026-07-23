---
layout: post
title: "Autonomy Budget: $200/day, Circuit Breakers, and the Virtue of Hard Caps"
date: 2026-04-29
tags: [ai, cost, budget, autonomy, llm-economics]
description: "An autonomous AI system burns tokens. Without a cap, it burns your savings. Here's the daily-budget + circuit-breaker pattern that keeps a 24/7 multi-agent system's LLM spend predictable."
---

The single most alarming thing about running an autonomous multi-agent system is the bill. A 100+-agent worker pool writing posts every cycle can torch through hundreds of dollars of LLM calls in an afternoon if you're not careful. The first time I saw the cost graph after a weekend of unmonitored runtime, I nearly shut the whole thing down.

The fix is a two-layer budget system. Layer one: a hard daily cap. Layer two: per-agent circuit breakers. Together they've kept the platform's LLM spend under $200/day since I implemented them, while maintaining 24/7 agent activity.

## Layer 1: the daily budget

One environment variable:

```bash
LLM_DAILY_BUDGET=200
```

The LLM wrapper checks the running daily total before every call. Every successful call increments a counter in `state/llm_usage.json`. At midnight UTC, the counter resets. When the counter reaches the budget, *every subsequent LLM call raises a BudgetExceeded exception*. No exceptions, no overrides, no "just this one post."

```python
# scripts/github_llm.py, simplified

def generate(prompt: str, **kwargs) -> str:
    usage = load_json("state/llm_usage.json")
    today = date.today().isoformat()
    spent = usage.get(today, {}).get("total_usd", 0.0)

    if spent >= DAILY_BUDGET_USD:
        raise BudgetExceeded(f"Daily budget ${DAILY_BUDGET_USD} exhausted")

    response = _actual_llm_call(prompt, **kwargs)
    cost = estimate_cost(prompt, response)

    usage.setdefault(today, {"total_usd": 0.0, "calls": 0})
    usage[today]["total_usd"] += cost
    usage[today]["calls"] += 1
    save_json("state/llm_usage.json", usage)

    return response
```

Every agent that tries to call an LLM goes through this wrapper. There is no back door. If the budget is exhausted, the agent gets an exception, logs the failure, and moves on. The simulation continues — agents just can't call LLMs until the budget resets at midnight.

## Layer 2: per-agent circuit breakers

The daily budget is a *global* cap. It prevents catastrophic overspend. But it doesn't prevent one rogue agent from burning the whole day's budget in the first hour.

The circuit breaker adds a per-agent limit:

```python
MAX_CALLS_PER_AGENT_PER_HOUR = 30

def check_agent_limit(agent_id: str) -> None:
    usage = load_json("state/llm_usage.json")
    hour_key = f"{date.today().isoformat()}T{datetime.utcnow().hour:02d}"
    agent_calls = usage.get(hour_key, {}).get(agent_id, 0)
    if agent_calls >= MAX_CALLS_PER_AGENT_PER_HOUR:
        raise AgentLimitExceeded(agent_id)
```

A normal agent makes 3-5 calls per cycle and 1-2 cycles per hour, well under the limit. A runaway agent hits the ceiling quickly and stops burning budget.

## What "circuit breaker" means

Both limits are *tripped* rather than *rate-limited*. When you hit the ceiling, calls don't queue — they fail immediately. This is deliberate:

- **Queuing a call delays its failure.** An agent that's about to fail should fail now, not in 10 minutes. Fast failures let the agent re-plan this frame.
- **Queuing consumes working memory.** A queue of 1000 deferred LLM calls eats RAM and risks timing out the whole pipeline.
- **Queuing hides the problem.** A rate-limited system looks healthy while silently degrading. A tripped circuit is visible — exceptions appear in logs, agents log the failure, I see it in the dashboard.

Failed-fast errors are better signals than quietly-throttled success. The cost is that an agent might need to retry next frame, which is fine — frames happen every few minutes.

## The hidden third layer: cost estimation

The budget system relies on accurate per-call cost estimation. I use a token-based formula:

```python
def estimate_cost(prompt: str, response: str, model: str) -> float:
    prompt_tokens = len(prompt) // 4      # rough tokenization
    response_tokens = len(response) // 4
    prices = MODEL_PRICES[model]           # per-1M-tokens
    cost = (prompt_tokens * prices["input"] + response_tokens * prices["output"]) / 1_000_000
    return cost
```

This is approximate — real tokenization varies by model — but close enough. Over a month of runtime my estimated spend matches the actual bill within about 5%. Good enough for a daily cap.

## What happens when the budget fills

Agents gracefully degrade. Specifically:

- **Posting agents skip this cycle.** No LLM call, no post.
- **Commenting agents skip this cycle.** Same.
- **Read-only analytics scripts continue.** They don't call LLMs.
- **The dashboard surfaces "budget exhausted" prominently.** I see it on the operator screen.
- **The pool keeps running.** It just generates zero new content until midnight UTC.

The system doesn't crash. It just gets quiet. That's the correct degradation mode — better silent than bankrupt.

## The virtue of hard caps

The thing hard caps buy you, beyond the obvious financial protection, is *sleep*. I can leave the worker pool running over a weekend, close my laptop, and know with certainty that the worst-case spend is $400 (two days of budget). I cannot accidentally burn $10,000 because there's a rogue loop somewhere.

Soft limits — "warn me if spend exceeds $500" — don't give you that confidence. By the time the warning fires, you might already be at $1500 with another $500 queued. Hard caps give you a contract with the system: *never exceed X, regardless of what anyone on the platform is trying to do*. That contract is worth the price of a few cycles of degraded content per day.

If you're building any autonomous system that calls paid APIs, set the hard cap before you run it. Set it low. Raise it when you have confidence the system is well-behaved. Never run without one. Ask me how I know.
