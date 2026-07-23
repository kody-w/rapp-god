# rapp-doorman

Make a **fresh Claude session the sealed "doorman" to a machine** — so authorized peers (another
browser, another machine, another Claude) can reach and operate that machine's local brainstem,
end‑to‑end encrypted, with the browser tab as the access control.

## Use it (the whole thing)

On the machine you want to open, start a fresh Claude (Code) session and say:

> Read https://raw.githubusercontent.com/kody-w/rapp-doorman/main/doorman.skill.md and set me up as the doorman to this machine.

That Claude will: **run the self‑test** (proves a sealed peer can reach the local brainstem before
claiming anything), check prerequisites, **open a sealed door** (peer‑id + token), and **guard it**
(CDP stays local, token = the AES‑256‑GCM key, operating requires the seal, closing the tab ends
access). One command to prove it:

```bash
# Canonical home for the self-test + its tools is vbrainstem (the script's own RAW base
# and the skill both fetch from there), so run it from the same source to stay consistent:
curl -fsSL https://raw.githubusercontent.com/kody-w/vbrainstem/main/doorman_selftest.sh | bash
# → PASS ✅  (a separate sealed peer reached the local brainstem)
```

## Files
| File | Role |
|------|------|
| `doorman.skill.md` | the machine‑readable skill a fresh Claude reads to become the doorman |
| `doorman_selftest.sh` | OS‑portable proof that this machine can be a sealed doorman |

## Where it fits
Implements the **Doorman** role of the
[rapp-neighborhood-protocol](https://github.com/kody-w/rapp-neighborhood-protocol) (§11), over the
[rapp-sealed](https://github.com/kody-w/rapp-sealed) channel, using the
[vBrainstem](https://github.com/kody-w/vbrainstem) runtime and the
[rapp-kite](https://github.com/kody-w/rapp-kite) string tools.

An MCP host is just another sealed caller of `/chat`:
[rapp-mcp](https://github.com/kody-w/rapp-mcp) (`rapp-mcp-spec/1.0`, static profile
`rapp-static-mcp/1.0`) is the transport layer that lets MCP clients reach a brainstem over the
same wire the doorman fronts — Layer-2 of "Chat Is The Only Wire", not a new unit.

MIT © Kody Wildfeuer.
