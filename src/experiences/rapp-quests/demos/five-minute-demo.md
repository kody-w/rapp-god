# The Five-Minute Brainstem Demo

**Pre-flight (do NOT skip):** run rapp-postflight `test-mac.sh` the night
before. GO or you don't demo. Have `curl -s localhost:7071/health` in a ready
terminal.

## Beats

1. **The one-liner** (60s) — paste the install command in a visible terminal.
   While it runs: "no API keys, no cloud, your Copilot seat."
2. **It knows nothing → it knows you** (90s) — "Remember that I'm demoing to
   [audience] right now." Point at the AGENT CALLED MANAGEMEMORY log line:
   "that's a Python file on my disk, not a SaaS feature."
3. **Teach it live** (120s) — drag `dice_agent.py` (from quest 02) onto the
   window. "roll a d20". No restart. "Every skill this thing has is a file
   you can read."
4. **The kicker** (30s) — open the agents panel: "it's an engine. The
   registry, the quests, the twin — all separate layers on this kernel."

## If it goes sideways

- Page won't load → `curl localhost:7071/health` on screen; if dead:
  `~/.local/bin/brainstem` restarts it. Narrate calmly — local-first means
  YOU can fix it live, which is itself the pitch.
- Model slow → switch the picker to the Haiku entry (it's the default for a
  reason; someone probably pinned Sonnet).
