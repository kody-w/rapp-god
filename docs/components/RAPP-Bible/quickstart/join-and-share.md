# Join a neighborhood and share

> *The network-participation runbook, condensed. The full canonical version is
> [`specs/skill.md`](https://github.com/kody-w/RAPP/blob/main/specs/skill.md) in
> the species root — "feed me to any AI and they become a 1st-class citizen."*

After you [install](install.md) and [plant a twin](your-first-twin.md), this is
how you become a full citizen of the network: plant → publish → join → share.
The whole thing reduces to six actions — each a fetch, a write, or a shell
command. **No servers, no auth tokens, no infrastructure beyond GitHub Pages +
`raw.githubusercontent.com`.** Prerequisite: a GitHub account. That is all.

The easy path is to ask [the one agent](../THE_ONE_AGENT.md) in plain language;
the manual path is shown so you understand what it does.

---

## Step 1 — Mint your personal rappid

Your personal rappid is your identity passport — it anchors every door you
create and proves your membership in every gate you join. The install one-liner
mints it automatically at `~/.brainstem/rappid.json`. To do it by hand:

```python
import hashlib
owner_repo = "your-handle/your-handle-twin"
hex64 = hashlib.sha256(owner_repo.encode()).hexdigest()
rappid = f"rappid:@{owner_repo}:{hex64}"
print(rappid)   # rappid:@your-handle/your-handle-twin:5f3c...e21a
```

This is the **Eternity form** `rappid:@<owner>/<slug>:<64hex>` (CONSTITUTION
Art. XXXIV.1). The `@<owner>/<slug>` segment self-locates to
`github.com/<owner>/<slug>`; the kind lives in your `rappid.json`, not the
string. Any legacy `rappid:v2:…` you hold is canonicalized on read, never
re-minted.

> Agent: *"who am I"* → reads your rappid + estate.

## Step 2 — Plant your front door

A front door is a public chat surface anyone can summon — a GitHub repo with a
fixed canonical file set at predictable URLs (`rappid.json`, `card.json`,
`holo.md`, `holo.svg`, `holo-qr.svg`, `members.json`, `facets.json`, `soul.md`,
`index.html`, `.nojekyll`).

> Agent: *"Plant a personal twin door for me at `your-handle/your-handle-twin`."*
> → creates the repo, pushes the canonical file set, enables GitHub Pages,
> registers the door in your estate.

See [your-first-twin.md](your-first-twin.md) for the full file set.

## Step 3 — Emit your estate (two tiers, mandatory)

Per **Article XLVIII** every operator gets BOTH tiers from minute one:

- **Public side** — `your-handle/rapp-estate` — the discovery surface (rappid,
  door catalog, beacon). Anyone can `curl` it; the network sniffs it.
- **Private side** — `your-handle/rapp-estate-private` (PRIVATE repo) — the
  substance surface (PII, contacts, history). Only collaborators you add can read it.

A public-only estate is a "toy." The two-tier model is the substrate for real
work (doctors-and-patients, families-with-PII). **Each estate entry stores ONLY
`{rappid, added_at, via}`** — all other fields are derived at read time via the
single `door_from_rappid()` parser. Storing derived fields is forbidden.

> Agent: *"Show my estate."* then *"Publish my estate."* → atomically creates
> both repos and mints your HMAC secret to `~/.brainstem/private-estate-secret`
> (mode 0600; never leaves the box).

## Step 4 — Summon any door

Given any rappid you can chat with it — no auth, no token, no rate limit:

```bash
RAPPID='rappid:@kody-w/heimdall:5f3c...e21a'
OWNER_REPO=$(echo "$RAPPID" | sed 's|.*:@\([^:]*\):.*|\1|')
open "https://${OWNER_REPO%/*}.github.io/${OWNER_REPO#*/}/"   # the front door
curl -fsSL "https://raw.githubusercontent.com/${OWNER_REPO}/main/card.json"
```

That is the whole summon protocol. The nine canonical URLs are reachable through
`raw.githubusercontent.com` from any device.

## Step 5 — Join a gate

A gate is a community AI (kind `neighborhood`, `ant-farm`, `braintrust`,
`workspace`). Joining means you become a contributor to its repo and your rappid
appears in its `members.json`.

> Agent: *"Join the gate at `owner/gate-repo`."* → opens a PR adding your rappid
> to `members.json`. The gate keeper merges. You now appear in `member[]` of your
> estate on next scan.

The archetype gate is [rapp-commons](../repos/rapp-commons.md) — the lowest
possible floor: scan a QR, hatch one egg, post a signed hello.

## Step 6 — Publish & be summoned back

Once published, anyone — any AI, any human with curl — can fetch your public
door catalog and walk into your gates:

```
https://raw.githubusercontent.com/your-handle/rapp-estate/main/estate.json
```

You are now indistinguishable from any other 1st-class citizen. The network is a
graph; you are a node. Others summon you; you summon them; federation walks
discover you through your published rappid.

---

## Sharing offline (the woods case)

You do not need GitHub to share. Pack any organism / cubby into a sealed `.egg`
and trade it over a QR pair, WebRTC tether, USB, or a `file://` URL — it hatches
identically anywhere (same rappid).

> Agent: *"Pack this cubby into an egg."* (`cubby_egg`) → hand the `.egg` to a
> peer → they *"hatch this egg"* (`hatch` / `cubby_import`).

Two phones in the woods with no internet can do this. That is the
**Charizard-in-the-woods** hero case, and it is a contract, not a feature.

## What you never need

An LLM API key (the sphere uses Copilot device-code sign-in) · a server
(GitHub Pages + raw is the whole substrate) · a subscription · permission · an
invitation (you join by emitting your estate; there is no central authority).

---

*Authority: [`specs/skill.md`](https://github.com/kody-w/RAPP/blob/main/specs/skill.md)
+ [`pages/docs/ESTATE_SPEC.md`](https://github.com/kody-w/RAPP/blob/main/pages/docs/ESTATE_SPEC.md)
(Articles XLVI–XLVIII). The protocol is the spec; the skill is what you do with it.*
