# PAYPHONE.md

### `rapp-payphone-dial/1.0` — the public dialer for **private (dark-door) RAPP neighborhoods**

> A **payphone** names no door. You walk up to a public box on the open web, drop in a **rappid**
> (the phone number, handed to you out-of-band), and it dials — using **your own** GitHub identity,
> not the payphone's. If you are a collaborator on that door you hear a **dial tone**; everyone else
> hears the same **404** as a wrong number. The payphone is *only the handshake*: it verifies you,
> fetches the sealed-channel key, and hands you into the live room. Nothing of the call passes
> through it.

This is the formal companion to [`NEIGHBORHOOD_PROTOCOL.md`](./NEIGHBORHOOD_PROTOCOL.md) **§19**
("the dark-door pattern"), where the payphone is introduced. It is a **profile of the one protocol**,
not a new one: it speaks the §6 envelope and enforces the §8 seal, and it composes the existing
primitives (§5 transports, §11 doorman, §18 front-door/relay) into the one path that lets a peer
reach a **door with no public front door**. It owns no new vocabulary beyond the proper noun
**Payphone**.

- **Trust:** key-possession + `gh`-collaborator standing only — PKI-free, consistent with the
  rappid eternity identity (`rappid:@owner/slug:<64hex>`, sha256 content-address, keypair *optional*,
  never required).
- **Substrate:** GitHub — raw CDN + Issues-mailbox + PR-consent + Pages-edge. No central server,
  no broker session; the WebRTC broker is handshake-only (SDP/ICE), data is DTLS peer-to-peer.
- **Constitution:** the resolver is `door_from_rappid()`, the **single legal rappid→door parser**
  (Art. XLVI); the dialer page is **privacy-clean** (Art. XLVII) — it names no door, stores no
  directory, holds no state.

---

## §1 — Definition (the Payphone role)

A **Payphone** is a **stateless, public, first-party HTTPS page** that turns a pasted **rappid**
into a live, sealed connection to that rappid's **door**, authenticating the **dialer** (the caller)
with the dialer's **own** GitHub account.

It sits beside the two access surfaces already specified in the neighborhood protocol and is
distinct from both:

| Surface | Spec | Names a door? | Holds state? | Reaches a **private** door? |
|---|---|---|---|---|
| **vNeighborhood front door** | `rapp-vneighborhood/1.0` (§18) | **yes** — one repo == one door | the repo holds the bones + log | no (public doors only) |
| **Doorman** | NEIGHBORHOOD_PROTOCOL §11 | yes — stands up *its* machine's door | the machine holds the brainstem | it **is** the door, from the inside |
| **Payphone** | `rapp-payphone-dial/1.0` (this spec) | **no** — generic, names nothing | **no** — parser + transport selector | **yes** — collaborator-gated |

The defining property: a **front door is one repo's lobby**; a **payphone is the whole town's pay
phone** — one box that can dial *any* door whose number you were given, including dark doors that
publish no lobby at all. Because it names nothing and stores nothing, the same deployed page dials
every door in the estate; there is exactly one payphone implementation, not one per neighborhood.

> **Why it exists.** A dark door (§19) has, by design, **no public front door** — the private repo
> 404s to outsiders, and wrong-number is indistinguishable from no-access. A peer (especially a
> **kited vTwin** in a browser, §5a-tether) therefore has no lobby URL to open. The payphone is the
> missing public on-ramp: the one page they *can* open, that reveals the door **only** to someone who
> proves they already belong.

---

## §2 — The dial flow (normative)

Dialing is a strict, ordered pipeline. Every step is performed **in the dialer's own browser/agent
with the dialer's own credential**; the payphone origin never sees a private name or a secret.

```
rappid  ──parse──▶  door_from_rappid()  ──guard──▶  tether ladder  ──key──▶  sealed room
(§2.1)              (§2.2, Art. XLVI)    (§2.3)      (§2.4)          (§2.5)    (§8)
```

### §2.1 — Input: the number

The only input is a **rappid** in canonical form (rappid eternity):

```
rappid:@<owner>/<slug>:<64-hex>
```

`<owner>` is a GitHub login, `<slug>` is the door slug (its first path segment is the repo), and the
`<64-hex>` is the sha256 content-address of the door's bones — the eternity identity, PKI-free. The
rappid is a **public address** (the species rappid rule, §19): knowing it confirms *nothing* about
the door's existence, contents, or membership. The dialer obtains it **out-of-band** — an invite egg,
a QR, or a message — exactly like being handed a phone number.

The payphone **MUST** read legacy rappid forms forever and emit only the canonical form (the RAPP
compatibility contract); the 64-hex content hash is the join key and is never rewritten in place.

### §2.2 — Resolve: `door_from_rappid()` (Art. XLVI — the single legal parser)

The rappid is resolved to a **DoorRef** by `door_from_rappid()`, the **only** Constitutionally-legal
way to turn a rappid into a door (Art. XLVI). No component may split, regex, or otherwise interpret a
rappid string by hand; all dialers call this one resolver so the mapping is identical everywhere and
testable (§6).

`door_from_rappid()` is **pure** — it performs **no network I/O** and consults **no directory**. It
deterministically derives every tether endpoint from the rappid alone. This is what keeps the
payphone stateless: there is nothing to look up and nothing to store.

```
door_from_rappid(rappid: str) -> DoorRef        # pure, total, no I/O
```

```jsonc
// DoorRef — the resolved door (rapp-payphone-dial/1.0)
{
  "schema":   "rapp-door-ref/1.0",
  "rappid":   "rappid:@kody-w/batcave:9f2c…",   // echoed, canonicalized
  "owner":    "kody-w",                          // GitHub login
  "repo":     "batcave",                         // first slug segment == repo
  "door_id":  "9f2c…",                           // the 64-hex content-address (seed)
  "tethers": {
    // 1) WebRTC live tether — a WELL-KNOWN peer id derived from the door (§19 lights)
    "webrtc":  { "channel":"5a-tether", "peer_id":"rapp-door-9f2c…(32 hex)" },
    // 2) Issues-mailbox — durable async fallback (§5b)
    "issues":  { "channel":"5b-issues", "repo":"kody-w/batcave",
                 "label":"rapp-dial/9f2c…(16 hex)" },
    // 3) PR-consent — open a pull request the door's doorman polls
    "pr":      { "channel":"5b-pr",     "repo":"kody-w/batcave",
                 "base":"main", "head_prefix":"rapp-dial/" },
    // 4) Raw fetch — static read of the door's bones/sealed log (read-only)
    "raw":     { "channel":"5a-raw",    "base":
                 "https://raw.githubusercontent.com/kody-w/batcave/main/.neighborhood/" }
  }
}
```

> **Derivation (reference, normative for `1.0`).** `peer_id = "rapp-door-" + door_id[:32]`;
> `label = "rapp-dial/" + door_id[:16]`; `raw.base = raw.githubusercontent.com/<owner>/<repo>/main/.neighborhood/`.
> All four are functions of the **rappid only**. A door **MAY** publish `addresses` in its
> `neighborhood.json` bones (§18) to override the derived endpoints, but those bones are themselves
> read over an **authenticated** fetch by the *dialer* (§2.4 raw step) — never by the payphone — so
> the override never reaches the public page.

### §2.3 — The guard (the 404 is the lock)

A private door's every endpoint **404s to outsiders**: the repo is private, so the API, raw CDN,
Issues, and PR surfaces all return *Not Found* to anyone without collaborator access. **Wrong-number
and no-access are indistinguishable** — the door's existence, contents, and membership are never
confirmed to an outsider. The 404 **is** the guard; secrecy does not depend on the rappid being
secret (it is a public address) but on collaborator gating.

The guard is lifted **only** by the dialer presenting **their own** GitHub credential:

- the dialer authenticates with `gh` (device-code OAuth, `gh auth token`, or an existing session)
  **in their own context** — the payphone holds **no** token and brokers **no** session;
- the dialer hits the **authenticated** GitHub API for the door's repo;
- **200 (readable) ⇒ collaborator ⇒ dial tone**; **404 ⇒ wrong number *or* not a collaborator**,
  reported identically. The payphone never distinguishes the two, by construction.

Collaborator standing is the **whole** authorization check. No allow-list, no central broker, no
keypair — `gh`-collaborator + the sha256 address, exactly the estate trust model.

### §2.4 — The tether ladder (offline-degrade order)

With the guard passed, the dialer attempts the **four tethers in fixed order**, most-live first,
falling through to the most-durable. The order is normative; a conformant payphone tries each until
one connects:

1. **`5a-tether` — WebRTC (live).** Connect to the door's well-known `peer_id` via a public broker
   (e.g. PeerJS). The broker carries **signaling only** (SDP/ICE); the session flows **DTLS
   peer-to-peer** — the broker never sees data and holds **no session**. If the door's **lights are
   on** (a kited host has claimed the peer id, §19), this is an immediate live room.
2. **`5b-issues` — Issues-mailbox (durable async).** If no live host answers, post the §6 envelope
   (sealed, §2.5) to the routing `label` on the repo; the door's doorman polls and replies. Nothing
   is lost; delivery is eventual (§5b). This is the GitHub mailbox.
3. **`5b-pr` — PR-consent.** Open a pull request from a `rapp-dial/` branch carrying the request
   envelope; merge/close **is** the door's consent decision (PR-consent as a first-class handshake).
   Used when a door wants an explicit, auditable accept rather than passive polling.
4. **`5a-raw` — raw fetch (static, read-only).** As the final degrade, authenticated-read the door's
   `.neighborhood/` bones + signed §6 log over the raw CDN. The dialer can **read** the room (the
   replicated board, §19) even when no peer and no doorman are live — the Pages-edge / raw-CDN floor
   that keeps the estate legible offline.

A dialer **MUST** try `5a-tether` before the fallbacks and **MUST** fall through on failure; it
**MAY** stop at the first success. All four are reached only **after** the guard (§2.3) — a
non-collaborator 404s on *every* rung.

### §2.5 — The key & the seal (admission == proof)

The live room is the **§8 sealed channel** (`rapp-sealed/1.0`, AES-256-GCM; key via PBKDF2-SHA256,
210 000 iterations) running end-to-end over the chosen tether. The channel **secret** is **fetched
from collaborator-readable material in the private repo** over the dialer's authenticated API call —
**never** from the broker, never from the payphone.

**Speaking the sealed channel IS the collaborator proof.** A non-collaborator who somehow reaches the
mesh cannot read the secret, so it can neither open a sealed message nor produce a valid one, and is
**silently dropped at admission**. The §2.3 404 is thus *lifted onto the live wire*: the same gate
that hid the door now gates the room. Rotate the secret to revoke; a **per-host epoch** yields
per-session keys.

After the seal is established the payphone's job is **over**: it has verified the dialer, fetched the
key, and handed off into the room. From here the dialer speaks §6 twin-chat directly with the door's
brainstem/twins — **the payphone is not on the call path.** ("Chat is the only wire," §3 — the
payphone is a *transport selector* for the dial, not a new wire.)

---

## §3 — Schemas

### §3.1 — `door_from_rappid()` contract

```
door_from_rappid(rappid: str) -> DoorRef
  PRE:  rappid matches the rappid eternity grammar (any legacy form is accepted, §2.1)
  POST: returns a rapp-door-ref/1.0 object whose tethers are pure functions of rappid
  PURE: no network, no filesystem, no clock, no directory — total and deterministic
```

This is the Art. XLVI single legal parser. Implementations are byte-equivalent across the estate
(brainstem, vBrainstem, the payphone page, a CLI) because they all import the same resolver.

### §3.2 — Dial request (what the dialer sends over a tether)

A dial is an ordinary §6 envelope of kind `dial`, wrapped (on a relay) in the signed
`rapp-commons-event/1.0` event (§6 on-relay form):

```jsonc
{ "schema":"rapp-twin-chat/1.0",
  "from_rappid":"rappid:@alice/twin:7b1e…",   // the DIALER's own rappid
  "to_rappid":"rappid:@kody-w/batcave:9f2c…", // the door (the number dialed)
  "utc":"2026-06-28T17:04:02Z",               // UTC-first frame
  "nonce":"…",                                 // replay guard; correlate the reply
  "kind":"dial",
  "payload":{ "tether":"5a-tether", "want":"admit" },
  "facets":[] }
```

### §3.3 — Dial result (what the payphone returns to its own UI)

The page reports only a coarse, **privacy-clean** outcome — never which of "wrong number" vs
"no access" produced a 404:

```jsonc
{ "schema":"rapp-dial-result/1.0",
  "rappid":"rappid:@kody-w/batcave:9f2c…",
  "outcome":"connected" | "no-answer" | "unreachable",  // NEVER "not-a-member" vs "no-such-door"
  "tether": "5a-tether" | "5b-issues" | "5b-pr" | "5a-raw" | null,
  "utc":"2026-06-28T17:04:03Z" }
```

`outcome:"unreachable"` is returned for **both** a non-existent door and a door the dialer cannot
access — the indistinguishability of §2.3 is preserved all the way to the UI.

---

## §4 — Boundary guarantees (Art. XLVII — privacy-clean)

The payphone is, and must remain, **a parser + a transport selector — nothing more**. These are
conformance-critical invariants:

1. **Names no private door.** The deployed page hard-codes **no** rappid, owner, repo, peer id, or
   label. Every door is supplied at dial time by the user. The page's source leaks no membership.
2. **Stores no directory.** It keeps **no** list of doors, no address book, no cache of who-is-where.
   `door_from_rappid()` is pure, so there is nothing to persist; the only "lookup" is the dialer's
   own authenticated API call against the door the user named.
3. **Holds no state & no session.** No accounts, no server-side sessions, no broker session. The
   PeerJS/WebRTC broker is **handshake-only** (SDP/ICE) and forgets the pair the moment DTLS is up;
   the data path is peer-to-peer. The payphone origin is **never** on the call path (§2.5).
4. **Holds no credential & no secret.** The dialer authenticates in **their own** context; the
   page never receives the dialer's token nor the door's channel secret. There is no privileged
   payphone identity to compromise or to subpoena.
5. **First-party + neutral.** Served from a first-party HTTPS origin (e.g. a Pages-edge); it is
   generic to the whole estate, so deploying or mirroring it discloses nothing about any door.

A change that would have the page remember a door, broker a session, or hold a token is a **boundary
violation** and fails conformance (§6).

---

## §5 — How it composes with the estate

- **NEIGHBORHOOD_PROTOCOL §19 (dark door).** The payphone is the **public on-ramp** to a dark door:
  §19 says members "reach it through a generic public dialer (`rapp-payphone-dial/1.0`)" — this spec
  *is* that dialer, made testable.
- **§18 (front doors / interchangeable relay).** A vNeighborhood front door is for **public** doors
  and *names* its door; the payphone is its dark-door dual and *names none*. Both hand a twin into
  the same §6/§8 room; `local ≡ kited ≡ cloud` relays are reachable through the §2.4 ladder
  unchanged.
- **§11 (doorman).** On the answering side, the door's **doorman** is what polls the Issues-mailbox,
  decides the PR-consent, and elects the kited host (§19 lights). The payphone is the **caller-side**
  counterpart to the doorman's **callee-side** guard — together they are the full dark-door call.
- **§5 transports / §8 seal / §6 envelope.** The payphone introduces **no new wire**. It selects
  among existing channels (`5a-tether`, `5b-issues`, `5b-pr`, `5a-raw`) and carries the existing §6
  envelope under the existing §8 seal. Chat is the only wire (§3).
- **rappid eternity.** Identity is the sha256 content-address; trust is `gh`-collaborator by default
  (`sig_suite: none`); the optional eternity keypair is **never** consulted by the payphone — opt-in
  sovereignty, not a requirement. PKI-free end to end.
- **The north star.** The payphone is how a peer **uses someone else's hardware**: you dial a
  neighbor's door from a bare browser and run on *their* brainstem. It is the connective tissue by
  which neighborhoods compose into the estate and the metropolis — the public box on every corner.
- **rapp-god.** `rapp-payphone-dial/1.0` registers in the rapp-god registry as a profile of
  `rapp-neighborhood-protocol/1.0`; the conformance vectors (§6) are mirrored into the
  neighborhood-protocol test suite so the dark-door dial path is **tested, not asserted**.

---

## §6 — Conformance vectors (testable, registered in rapp-god)

A payphone conforms to `rapp-payphone-dial/1.0` iff it passes every vector. These extend
NEIGHBORHOOD_PROTOCOL §16 / §19 conformance and are the canonical test of the **dark-door dial
path**.

| # | Vector | Required behavior |
|---|---|---|
| **V1** | `door_from_rappid()` purity | Given a fixed rappid, returns a byte-identical `rapp-door-ref/1.0` with **zero** network/file/clock access. Same output in brainstem, vBrainstem, CLI, and the page. |
| **V2** | Legacy rappid acceptance | Reads every historical rappid form (the compatibility contract); emits only canonical; the 64-hex hash is unchanged. |
| **V3** | Outsider 404 (the guard) | A dialer with **no** collaborator access gets `outcome:"unreachable"` on **all four** tethers; a non-existent door yields the **same** result. The two are indistinguishable in `rapp-dial-result/1.0`. |
| **V4** | Collaborator dial tone | A collaborator dialer reaches the live room: V4a host present ⇒ `5a-tether`; V4b host absent ⇒ falls through to `5b-issues` and the envelope lands on the label; V4c read-only floor ⇒ `5a-raw` returns the signed §6 log. |
| **V5** | Ladder order | Tethers are attempted in the order tether → issues → pr → raw; a failure at rung *n* falls through to *n+1*; success may stop. |
| **V6** | Seal == proof | A non-collaborator that reaches the mesh cannot derive the §8 key, cannot produce a valid sealed message, and is **silently dropped at admission** (no error oracle). |
| **V7** | Names nothing | Static analysis of the deployed page finds **no** rappid/owner/repo/peer-id/label literal and **no** persisted directory or token. (Art. XLVII.) |
| **V8** | No broker session | After DTLS is established, killing the broker does **not** drop the call; the payphone origin is provably absent from the data path. |
| **V9** | UTC frames | Every emitted envelope/result carries a UTC-first `utc`; correlation is by `nonce`. |
| **V10** | Revocation | Rotating the collaborator-readable secret (or advancing the host epoch) makes a previously-admitted non-collaborator's next dial fail at admission. |

Vector fixtures live alongside this file (`./vectors/payphone/`) and are referenced by the rapp-god
entry for `rapp-payphone-dial/1.0`.

---

## §7 — Worked example

**Scene.** Kody runs a **dark-door** workshop: the private repo `kody-w/batcave` *is* the
neighborhood (§19). It publishes **no** front door — every URL 404s to outsiders. Alice is a
collaborator; she got the number out-of-band in an invite egg:

```
rappid:@kody-w/batcave:9f2c4a…e1   (64-hex sha256 of the door's bones)
```

She is on her phone, in a plain browser tab — a **kited vTwin**, no install.

**1. Open the box.** Alice opens the public payphone page (a first-party Pages-edge URL). The page
names no door; it is just a dial pad.

**2. Drop the number.** She pastes the rappid. The page calls `door_from_rappid()` (Art. XLVI),
which **purely** derives the DoorRef — `repo: kody-w/batcave`, `peer_id: rapp-door-9f2c4a…`,
`label: rapp-dial/9f2c4a…`, `raw.base: …/batcave/main/.neighborhood/` — **without touching the
network**. The page still knows nothing about whether the door exists.

**3. Prove herself.** The page asks Alice to authenticate with **her own** GitHub (device-code in
her own context). Her browser hits the **authenticated** API for `kody-w/batcave`. Because she is a
collaborator → **200**. (Had she not been — or had the door not existed — she'd get **404**, reported
as `outcome:"unreachable"`, the two cases indistinguishable.)

**4. Climb the ladder.** The page tries the tethers in order. A teammate already opened the door, so
a **kited host** holds the well-known `peer_id` (lights ON, §19): rung 1 (`5a-tether`) connects over
**WebRTC**. The PeerJS broker passes only SDP/ICE; Alice's data flows **DTLS peer-to-peer**. (Had the
lights been off, the page would have fallen through to the **Issues-mailbox**, then **PR-consent**,
then a read-only **raw** view of the signed log.)

**5. Seal & hand off.** Alice's browser reads the **collaborator-only** channel secret from the
private repo over her authenticated API call (never the broker, never the payphone) and opens the
**§8 sealed** room. Her first sealed message **is** her proof of membership; a non-collaborator who
reached the mesh would be **silently dropped** here. The **payphone is now done** — it verified her,
got her the key, and stepped off the line.

**6. In the room.** Alice now speaks **§6 twin-chat** directly with the batcave's brainstem and the
other twins — running on **Kody's hardware**, from a bare phone tab, with nothing but a number she
was handed and her own GitHub account. The payphone box she used names no door, stored no directory,
and held no part of the call. A stranger who finds that same public box and pastes the same rappid
hears only a 404.

---

## §8 — Compatibility & versioning

- **`spec_id`:** `rapp-payphone-dial/1.0`. The version string is **never** edited in place; new
  capabilities are added as new fields / new vectors, and a breaking change mints `…/2.0`.
- **Reads forever:** the payphone honors every legacy rappid form and emits only canonical
  (compatibility contract). The 64-hex content hash is the durable join key.
- **One implementation:** because the page names nothing and stores nothing, a single deployed
  payphone serves the whole estate; mirroring it (Pages-edge, IPFS, a local file) is safe and
  discloses nothing — the un-shutdownable property follows from there being nothing private to host.

*Profile of `rapp-neighborhood-protocol/1.0` (§19). Resolver mandated by CONSTITUTION Art. XLVI;
privacy boundary by Art. XLVII. PKI-free; `gh`-collaborator + sha256. Registered in rapp-god.*
