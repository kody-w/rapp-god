# rionet

**The agent-built web** — the federation layer: `rapp.robots.txt` → rappbot → RIO.

- Canonical: https://github.com/kody-w/rionet
- Default branch: `main`

## What it is

RIONet is the **federation layer of the agent-built web** — the network that [rio](rio.md) (the browser) navigates. The pipeline is: a site declares itself with `rapp.robots.txt` → the `rappbot` crawler walks it → a PageRank-style ranking (`rappPageRank`) orders the markdown pages → RIO serves the result.

It is the agent-native analog of the human web's robots.txt + crawler + ranking + browser stack, but built for agents producing and consuming markdown.

## What it provides

- `rapp.robots.txt` — how a site joins the agent-built web.
- `rappbot` + `rappPageRank` — the crawler + ranking.
- The federated index RIO reads.

Pairs with [rio](rio.md). Both live at OSI Layer 7 (see [`OVERVIEW.md`](../OVERVIEW.md) §4).
