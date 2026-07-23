# rapp-support

Support home for the [RAPP Brainstem](https://github.com/kody-w/rapp-installer).
File issues here — the grail repo's tracker stays reserved for engineering work
on the kernel and installers.

## Getting help

1. **In-app**: click **Get Help** in the brainstem UI — it can generate a
   diagnostics file (`share-with-admin` JSON) that tells your whole story.
2. **Here**: open a [help request](../../issues/new?template=help-request.yml)
   and attach that file. It contains your config, auth *state* (never tokens),
   loaded agents, and recent events — everything needed to help you fast.

## Quick self-service

| Symptom | First move |
|---|---|
| Browser says "can't reach this page" | Wait a few seconds and refresh — then `curl localhost:7071/health` |
| "sign in" in the header | Click it, or visit `localhost:7071/login` |
| Agent didn't load | Filename must match `agents/*_agent.py`, class must extend `BasicAgent` |
| Need a fresh start | `curl -fsSL https://kody-w.github.io/rapp-installer/install.sh | bash` |
| Fresh start didn't fix it | Full reset: [rapp-postflight](https://github.com/kody-w/rapp-postflight) `reset-mac.sh` / `reset-windows.ps1` |
