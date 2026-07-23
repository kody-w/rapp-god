# Build your first twin

A **twin** (organism) is one planted seed — a GitHub repo with its own Eternity
rappid, a soul, a body of agents, a memory, and a front door. The Tier-3
examples in this Bible (heimdall, echo, lumen, tide, kody-twin) are all twins.

A twin is the **organism scale** of the fractal: same five primitives (rappid +
door + card + tether + trust scope) as an agent below it and a neighborhood
above it. See [`OVERVIEW.md`](../OVERVIEW.md) §2.

## What a twin is

- A GitHub repo that **is** the organism — its identity (`rappid.json`), its
  voice (`soul.md`), its body (`agents/`), its memory (`.brainstem_data/`), its
  skin (`index.html` + the doorman). All committed files; no server runs.
- Its own **Eternity rappid**, minted once: `rappid:@<owner>/<slug>:<64hex>`.
- A `parent_rappid` pointing at the species root (or your operator rappid) —
  this is its lineage.
- An optional `.egg` so others can hatch a copy locally (same rappid, anywhere).

## The easy path (the one agent)

With [the one agent](../THE_ONE_AGENT.md) installed, just ask:

> *"Plant a personal twin door for me at `your-handle/your-name-twin`."*

The plant flow mints the rappid, writes the soul, scaffolds the canonical file
set, enables GitHub Pages, and registers the door in your estate.

## The manual path (the canonical file set)

Create a GitHub repo and push these files at root:

| File | Content |
|---|---|
| `rappid.json` | `{"schema":"rapp-rappid/2.0","rappid":"rappid:@your-handle/your-name-twin:<64hex>","kind":"twin","parent_rappid":"<your-operator-rappid>","kernel_version":"0.6.0", …}` |
| `soul.md` | The Identity block — *"read this every turn"* (`rapp-twin-spec/1.0`). **Never** falls back to "RAPP" / "an AI assistant" (ANTIPATTERNS §4). |
| `card.json` | The holocard (`rapp-card/1.0`), deterministic from the rappid. |
| `holo.svg` / `holo-qr.svg` | Avatar + summon QR, generated from the rappid seed. |
| `holo.md` | A friendly single-page entry doc. |
| `members.json` | `{"members": []}` for a twin (gates ship a real roster). |
| `facets.json` | `{"schema":"rapp-facets/1.0","facets":{}}` — declare published capabilities as you add them. |
| `index.html` | The sphere (the front-door chat surface). |
| `.nojekyll` | Empty file — required so GitHub Pages serves `index.html` verbatim. |
| `README.md` | Human-readable description. |

Then enable GitHub Pages (Settings → Pages → Source: main, /). The door is live
at `https://your-handle.github.io/your-name-twin/`.

## Mint the rappid

```python
import hashlib
owner_repo = "your-handle/your-name-twin"
hex64 = hashlib.sha256(owner_repo.encode()).hexdigest()
rappid = f"rappid:@{owner_repo}:{hex64}"
```

## Estate

Every operator gets a two-tier estate (public + private) from minute one. Your
new twin's rappid lands in `created[]` of your estate. See
[ESTATE_SPEC](../SPEC/kernel/ESTATE_SPEC.md) and
[join-and-share.md](join-and-share.md) step 3.

## Reference twins

- [heimdall](../repos/heimdall.md) — the canonical twin example
- [echo-brainstem](../repos/echo-brainstem.md) — pattern synthesizer
- [lumen-brainstem](../repos/lumen-brainstem.md) — chronicler
- [tide-brainstem](../repos/tide-brainstem.md) — rhythmic voice
- [kody-twin](../repos/kody-twin.md) — operator front door

## Next

- [Join a neighborhood and share](join-and-share.md)
- [Build your first rapplication](your-first-rapplication.md)
