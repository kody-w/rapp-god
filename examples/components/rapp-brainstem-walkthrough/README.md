# RAPP Brainstem — The Interactive Walkthrough

**Run it:** https://kody-w.github.io/rapp-brainstem-walkthrough/

The real brainstem UI — byte-identical `index.html` from the product — running
**"The First Interview"**, its 14-step guided tour, entirely in your browser.
Two tiers, same page:

- **Training copy (default)** — no server, no Python, no GitHub account, no
  dependencies: a simulator shim answers the brainstem's own API calls
  (`/chat`, `/chat/stream`, `/agents`, the RAR registry) from canned,
  in-browser state. The tour starts on its own. Memory persists in
  `localStorage`; append `?reset` to start fresh.
- **Live (sign in to unlock)** — click *"sign in with GitHub to go live"*
  (bottom left) and the page becomes a REAL brainstem: the vBrainstem engine
  (`brainstem_web.py`, kody-w/vbrainstem's faithful port of
  `rapp_brainstem/brainstem.py`) boots in a Pyodide Web Worker, GitHub
  device-code auth runs for real, and `/chat` answers with your Copilot
  models executing real agents. No auth → the simulator keeps answering;
  a failed Pyodide boot falls back to the simulator too.

Everything in the tour works for real against the simulation:

- **Memory** — introduce yourself, clear the chat, and it still knows you
- **Agent surgery** — export, delete, and drag-drop-restore a live agent file
- **Honesty** — ask for what it can no longer do and watch it say so
- **The registry** — install `@rapp/learn_new` (SHA-256 verified in-page)
- **Creation** — describe an agent in plain words; the file is written and hot-loaded

When trainees finish, the real thing is one line away:

```bash
curl -fsSL https://kody-w.github.io/rapp-installer/install.sh | bash
```

## Also here: the produced video

[**video.html**](https://kody-w.github.io/rapp-brainstem-walkthrough/video.html) —
all 14 steps of the [full RAPP guide](https://github.com/kody-w/rapp-installer/blob/main/skill.md)
(clean machine → Teams/M365 Copilot) as one produced walkthrough video with
seekable chapters, filmed on real surfaces with [RAPP Video](https://kody-w.github.io/rapp-video/).

## Rebuilding the page

```bash
python3 tools/build.py   # stock brainstem index.html + tools/sim_shim.js → index.html
```

The build injects `tools/sim_shim.js` + `tools/live_bridge.js` as the first
`<script>` after `<body>` and embeds the preinstalled agent files plus a
10-agent RAR catalog subset (real bytes, digests recomputed to match). The
stock UI is never edited. The live tier's engine files
(`vbrainstem-worker.js`, `brainstem_web.py`, `local_storage.py`, `soul.md`,
`agents/`) are copied from [kody-w/vbrainstem](https://github.com/kody-w/vbrainstem)
— one documented delta: `hacker_news_agent.py` is added to the worker's seed
set so the tour's agent-surgery arc has its subject in live mode.

---

<sub>RAPP and the RAPP family of names are trademarks of the RAPP project. Code is
MIT-licensed; see [DISCLAIMER.md](DISCLAIMER.md).</sub>
