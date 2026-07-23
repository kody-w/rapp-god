# rapp-brainstem-sdk

**Run a brainstem** — the headless SDK serving the `brainstem.py` `/chat` contract.

- Canonical: https://github.com/kody-w/rapp-brainstem-sdk
- Default branch: `main`

## What it is

The headless brainstem. Where [vbrainstem](vbrainstem.md) runs a brainstem in a browser, `rapp-brainstem-sdk` runs one with no UI at all — it serves the canonical `POST /chat` contract from `brainstem.py` as a library / embeddable surface. Use it to embed a brainstem inside another program, a service, or a test harness.

## What it provides

- The headless `/chat` surface (`rapp-chat-response/1.0`).
- The same single-file agent contract as Tier 1 — agents run unmodified.

This realizes the tier-portability guarantee: an agent that runs in the local brainstem runs unmodified here.
