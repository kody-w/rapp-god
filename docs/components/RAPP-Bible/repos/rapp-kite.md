# rapp-kite

**Channels & trust** — the string: fly and operate kited twins.

- Canonical: https://github.com/kody-w/rapp-kite
- Default branch: `main`

## What it is

A **kited twin** is a twin that doesn't run on the operator's own machine — it runs somewhere reachable (a cloud relay, another device) and is *operated remotely*, like a kite on a string. `rapp-kite` is the string: the toolkit for flying and operating those kited twins.

This is the "warm" travel mode from the Master Plan — the agents are fetched and run remotely while state stays home. The kited twin has its own neutral visual identity (a kite), defined in [rapp-kited-twin](rapp-kited-twin.md).

## What it provides

- The operator-side controls for a remote (kited) twin.
- The interchangeable-relay property: local ≡ kited ≡ cloud — same `/chat` contract, different substrate.

Pairs with [rapp-doorman](rapp-doorman.md) (the sealed door) and [rapp-resident](rapp-resident.md) (the permanent cloud relay).
