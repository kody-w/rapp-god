# 👁️ rapp-god

**The registry of the RAPP "god" — and every version of every part it's made of.**

[RAR](https://github.com/kody-w/RAR) is a registry of agents. **rapp-god is a registry of the whole
ecosystem**: the kernel, the installer, the spec, the codec, the seed agents — every load-bearing
part. And for each part it keeps **every version** it has ever seen, as an immutable,
content-addressed frame. Nothing is ever deleted.

**Live:** <https://kody-w.github.io/rapp-god/> · **Badge:** ![rapp-god](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fkody-w%2Frapp-god%2Fmain%2Fapi%2Fv1%2Fbadge.json)

## The idea

- **Every version is a load-bearing fallback.** Each distinct version of a part lives forever at its
  own raw URL (`versions/<part>/<sha8>`). If a canonical source breaks, vanishes, or ships a bad
  update, you pin to any prior frame and keep going. Not just the current version — *all* of them.
- **Update detection, never coercion.** When your copy's hash differs from the grail's current
  version, that's just *an update waiting*. You see it; you decide. Stay on your frame indefinitely
  if it's the one that works.
- **It observes; it never fixes.** A fork doesn't get auto-reconciled — a drifted copy might be the
  better one. rapp-god shows you *exactly what drifted* (hash + inline diff) and leaves the call to you.
- **Fully static.** No server. The dashboard reads `registry.json`; everything is served globally
  over `raw.githubusercontent.com`.

## What it found on day one

| | |
|---|---|
| parts tracked | **20** |
| versions held (fallback frames) | **75** |
| `install.sh` versions archived | **24** (full git history) |
| `brainstem.py` (kernel) versions | **25** |
| forked across repos | **8** |
| frozen kernel (`brainstem.py`, `VERSION`) | ✅ holding — grail == RAPP |

The kernel discipline is holding; the installer scripts, both memory agents, RAR's `basic_agent`
copy, and the neighborhood spec have forked. All of it was invisible before.

## The static API — built entirely on raw.githubusercontent.com

No backend. Fetch these from anywhere:

| Endpoint | What |
|---|---|
| [`registry.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/registry.json) | the full index — every part, every version, which source is on which version, raw fallback URLs |
| [`api/v1/status.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/status.json) | the latest verdict (summary + per-part drift) |
| [`api/v1/badge.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/badge.json) | shields.io endpoint badge |
| `versions/<part>/<sha8>` | **the fallback** — any version's exact bytes, immutable, pinnable forever |

**Check for an update** (stay or take it — your call):
```bash
GRAIL=$(curl -s https://raw.githubusercontent.com/kody-w/rapp-god/main/registry.json \
  | jq -r '.parts[]|select(.name=="install.sh").grail_sha8')
MINE=$(shasum -a256 install.sh | cut -c1-12)
[ "$GRAIL" = "$MINE" ] && echo "up to date" || echo "an update is waiting (grail $GRAIL)"
```

**Pin a fallback** — fetch one exact, immutable version:
```bash
curl -O https://raw.githubusercontent.com/kody-w/rapp-god/main/versions/install.sh/<sha8>.sh
```

## Build it

Like RAR: `manifest.json` is the hand-authored input, `build_god.py` is the only build step,
`registry.json` is generated (never hand-edited).

```bash
python3 build_god.py        # fetch every source + git history, capture new frames, regenerate the registry + API
python3 build_god.py --no-net   # regenerate from already-captured frames only
```

`manifest.json` lists the **parts** — each with a `grail` (the source of truth) and its `mirrors`,
plus `"history": true` to archive the grail's full git history, and `"kind"`:
- **`observe`** (default) — record drift, never fail CI. The drifted copy might be the keeper.
- **`enforce`** — fail CI on drift. Opt-in, per part, only once you've decided it must never differ.

CI (`.github/workflows/god-build.yml`) runs `build_god.py` on every push and every 6h, commits any
new frames + registry changes (and *only* when something actually changed), and **stays green** —
drift is published, never enforced.

## The grail pattern

RAPP's own canon calls the frozen kernel "the v0.6.0 **grail**," and instances "fetch from grail."
`rapp-installer` is that grail; RAPP mirrors it (its `test_plant.sh` literally `diff`s planted files
against `raw.githubusercontent.com/kody-w/rapp-installer/main`). rapp-god generalizes that private
grail-diff into a **public, global, per-file, every-version** registry.

Part of the RAPP ecosystem — see the [map](https://github.com/kody-w/rapp-map). MIT © Kody Wildfeuer.
