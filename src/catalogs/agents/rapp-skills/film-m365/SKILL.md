---
name: film-m365
description: Film a Copilot Studio agent in the REAL M365 Copilot surface — the ONLY sanctioned way to make agent demo videos. Playwright drives a dedicated authed Chrome profile, records the page via CDP (no screen capture, no desktop takeover), then trims, dead-time-compresses, and gate-verifies to GO. Use when Kody says "film <agent>", "make a video of <use case>", "location shoot", or any ask for an agent demo video. NEVER use the synthetic stage — qa_gate blocks it (synthetic-stage check).
---

# Film an agent in real M365 Copilot

The one sanctioned path for agent demo videos (Kody's ruling 2026-07-16: staged
renders "look junky"; `director/qa_gate.py` NO-GOs them via the `synthetic-stage`
check). Proven end-to-end on a full location shoot (GO).

Work repo: your agent project repo (= $REPO). Python: `$REPO/.venv-local/bin/python`
(has Playwright). Reference scripts from the proven shoot (copy + adapt; treat as
the canonical implementation): `auth_bootstrap.py`, `film_take_v3.py`,
`gate_and_tighten.sh`, `postprod.sh` from a prior shoot's scratchpad. If gone,
rebuild from the spec below (it is complete).

## 0. Preconditions (fail fast, in order)
1. **Agent reachable in M365 Copilot**: published in Copilot Studio with
   **Authenticate with Microsoft** (Dataverse `bots.authenticationmode = 2` — mode 1
   breaks connected-agent calls AND the M365 channel), Teams+M365 channel added,
   agent added from the store for the filming account. Orchestrator + ALL child
   agents must share the same auth mode (`ConnectedAgentAuthMismatch` otherwise).
   Republish order: children first, orchestrator last.
2. **One-screen answer rule** in the agent's instructions (Kody's law): responses
   ≤ ~100 words / one viewport. Patch instructions via Dataverse PATCH + PvaPublish,
   save prestate sha256, wait ~90s, REVERT after the shoot (prestate sha must match).
3. **Dedicated browser profile** at `~/.rapp-director/chrome-profile` (mode 700).
   If stale/absent: run the auth bootstrap (headed Playwright, real Chrome channel,
   agent deep-link) and have KODY do the passkey/MFA sign-in — never touch
   credentials yourself; Authenticator number-match prompts may hit his phone on
   relaunches. Session persists; warm relaunches usually skip MFA.
4. Agent deep-link: `https://m365.cloud.microsoft/chat/agent/<titleId-pair>?titleId=…`
   (from Copilot Studio's "See agent in Microsoft 365" link).

## 1. The take (single Playwright script, CDP video — desktop stays Kody's)
- `launch_persistent_context(profile, channel="chrome", headless=False,
  viewport=1728x1117, device_scale_factor=2, record_video_dir=…,
  record_video_size=3456x2234, args=[--disable-blink-features=AutomationControlled,
  --disable-backgrounding-occluded-windows])`. Do NOT force --window-size/position
  (causes gray letterbox band).
- goto deep-link → wait for composer `[aria-label*="Message"], [placeholder*="Message"]`.
- **Fresh chat**: if main innerText > 400 chars, `goto` the deep-link again.
  NEVER click the global "New chat" — it silently drops you into vanilla Copilot
  (the take-2 wrong-subject failure).
- **SUBJECT-IDENTITY GATE (mandatory)**: abort unless the composer placeholder
  names the agent (`[placeholder*="<Agent Name>"]`). Never film without it.
- **Collapse the nav sidebar** (PII: agent list, chat history, account name):
  `button[aria-label*="ollapse navigation"]`. The hover tooltip ("Expand navigation")
  lingers until the next mouse move — trim covers it.
- Per question: click composer → `page.keyboard.type(q, delay≈65)` → Enter →
  **scroll-follow while streaming** (`page.mouse.move(864,480)` +
  `page.mouse.wheel(0,900)` every ~2.2s) → settle = main innerText length stable
  3 consecutive samples. Questions carry the one-screen constraint implicitly via
  the patched instructions; keep them demo-grade (a "what can you do" + one
  end-to-end scenario walkthrough).
- **Outro**: wheel to top, then ~18 × wheel(0,420) at 0.75s — slow pan through the
  whole conversation. Hold 4.5s. Close context (flushes video webm).
- Save DOM screenshots + main innerText transcript per question for QA/report.

## 2. Post + QA gate (the film is not done until GO)
1. Sample frames across the WHOLE timeline and READ them (Read tool). Every real
   defect so far was invisible in logs: below-the-fold answer, wrong agent, MFA
   screen with tenant UPN, PII sidebar, letterbox, lingering tooltip.
2. Trim the head to the first clean-rail, tooltip-free frame (auth/redirect and
   sidebar-collapse frames must go). `ffmpeg -ss T -i take.webm -c:v libx264
   -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart out.mp4`.
3. `python3 director/qa_gate.py <film> --no-audio-required [--transcript t.json]`.
   - `blank-frozen-spans` NO-GO → dead-time compression: cut each flagged span
     keeping first 1.5s (`select='not(between(t,a,b)+…)',setpts=N/FRAME_RATE/TB`),
     re-gate (≤3 rounds). Alternative for a static tail: 8s zoompan push-in outro.
   - If a transcript is supplied and cuts shorten the film, remap turn timestamps
     through the cutlist (t' = t − cut_time_before_t) into `*_edited.json` — the
     gate binds film duration to the transcript timeline by design.
4. Deliverable: `director/dist/<Agent>_Location_v<N>.mp4` (dist/ is gitignored —
   films stay local). Commit ONLY `director/qa/<slug>/EVIDENCE.md` evidence.
   If the repo requires an org token to push, push with that token explicitly —
   never a plain push under the wrong account.
5. Open the film for Kody (`open <film>`), report which frames you actually read.

## Known traps (each cost a take)
- Global "New chat" ⇒ wrong agent. Deep-link re-goto instead + subject gate.
- No scroll-follow ⇒ money answer streams below the fold, never on camera.
- Warm-profile relaunch may still re-MFA (Conditional Access) — warn Kody.
- M365 recent-prompts dropdown may flash earlier take questions (benign, no PII).
- Co-sessions may hold the repo: check `git status` before editing shared files;
  own only your files; single commit at the end; token-push, never plain push.
