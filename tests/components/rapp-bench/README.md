# rapp-bench

Latency + behavioral regression harness for a **running** RAPP brainstem
(`localhost:7071`). Nothing here talks to any API except your own local server.

## Why

v0.6.5 made Haiku the default model on the claim that it responds faster than
Sonnet. `bench.py` turns that claim into a measured number you can put on a
slide — and re-check on every plan/model-catalog change.

## Latency

```bash
python3 bench.py --models claude-haiku-4.5 claude-sonnet-5 --runs 5
```

Prints a markdown table (median/min/max per model), saves JSON to `results/`
(gitignored — commit a result only when you want a record). By default the
model setting is restored to `auto` afterwards; if you run a pinned model,
pass `--restore <your-id>`.

## Behavioral goldens

```bash
python3 golden.py
```

Each `golden/*.json` is a prompt + strings the response must contain (+
optionally an agent that must have been called). Run after soul edits, agent
changes, or model switches. Add a case per bug you never want back.

Pairs with [rapp-postflight](https://github.com/kody-w/rapp-postflight):
postflight gates the *installer*, bench gates the *chat*.
