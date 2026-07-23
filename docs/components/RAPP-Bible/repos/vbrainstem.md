# vbrainstem

**Run a brainstem** — the browser-native runtime (Pyodide, no install) + the tethered multi-participant surface.

- Canonical: https://github.com/kody-w/vbrainstem
- Live surface: https://kody-w.github.io/RAPP/pages/vbrainstem.html
- Default branch: `main`

## What it is

vbrainstem runs a brainstem **in the browser** with no install — Pyodide loads the Python agents in-page. There are two related surfaces:

- **The runtime** — a browser-native brainstem so anyone can run agents without installing anything.
- **The tethered surface** (`pages/vbrainstem.html`) — a multi-participant, QR-paired session. Two devices pair via QR (PeerJS broker → WebRTC data channel, ECDSA P-256 keypair + 6-digit safety code); both screens stay synced; an autonomous Coordinator twin drives a debate workflow. Three exchangeable LLM backends: localhost `:7071`, `?brainstem=URL`, or `?copilot=1` (Pyodide agents + Copilot via the Doorman).

The live session **is** a `brainstem-egg/2.3-session` cartridge — exportable as an `.egg`. That is how a live tether becomes portable (see [`SCHEMAS.md`](../SCHEMAS.md), the egg family).

## What it provides

- A zero-install browser brainstem.
- QR-pair WebRTC tethering with a safety code.
- Live session capture / export as a session egg.

Voice-first by default — "Listening…" on first load is correct UX.
