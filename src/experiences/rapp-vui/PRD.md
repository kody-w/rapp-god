# RAPP VUI — Product Requirements Document

*Status: draft v1 · Owner: Kody Wildfeuer · Part of the RAPP platform*

## 1. Summary

**RAPP VUI (Virtual UI)** is a hands-free, spatial interface for talking to a
RAPP Brainstem. You **look at what you want and pinch to select**; you speak and
it answers out loud. An immersive 3D scene with a living AI presence replaces the
keyboard-and-mouse chat window.

## 2. The one principle (do not lose this)

**The gesture loop IS the product.** Face/eye tracking moves a cursor; a hand
**pinch** selects. *Look at a portal → pinch → enter.* Everything else —
aesthetic, voice, the guided tour — is secondary and must never get in the way of
making that one interaction feel effortless. Build and tune it first, alone.

## 3. Problem / why now

- Chat UIs are keyboard-bound and screen-bound.
- The RAPP Brainstem is a local, hands-free-capable agent engine; it deserves an
  ambient, demoable interface.
- Gaze + pinch + voice is a genuinely new way to work with a local AI — and it
  runs entirely on-device (camera never leaves the machine).

## 4. Users

- The maintainer demoing RAPP hands-free (kiosk, stage, ambient desk).
- Anyone who wants to talk to a local AI without typing (accessibility, ambient).
- Any AI/agent that speaks the `/chat` protocol — the VUI is just a client.

## 5. Goals

- **Effortless gaze + pinch selection** (the bar).
- Voice in / voice out, with **barge-in**.
- A **living 3D presence** that reacts to state and evolves with the conversation.
- Runs **standalone** (canned demo) and against a **live brainstem with zero code
  change**.
- **Apple-grade, minimal** aesthetic.

## 6. Non-goals (explicitly dropped — do not build)

- ❌ Nested iframes / per-turn bytecode injection.
- ❌ Browser back-button history, time-travel, frame stacks, rewind.
- ❌ A dense keypad of buttons.
- ❌ Emojis anywhere.

## 7. Functional requirements

### 7.1 Input modalities
| Modality | Role | Notes |
|---|---|---|
| **Gaze** (MediaPipe face) | primary pointer (hands-free) | smoothed cursor; stable, no jitter mis-selects |
| **Pinch** (MediaPipe hand) | primary select | thumb-index pinch = select, release = deselect |
| **Voice** (Web Speech) | input + output | hold-to-talk STT; **barge-in** — talk over TTS → it stops & listens |
| **Mouse** | fallback menu ONLY | native cursor + click; **no gaze glow / dwell ring in mouse mode** |
| **Dwell** | optional gaze fallback | stare-to-select for gaze users with no free hand |

### 7.1.1 Two modes (DECIDED — do not auto-blend)

Auto-blending hand-pointing and head-pointing in one loop is confusing and
untunable. Ship **two explicit, toggleable modes**, each optimized alone:

- **Gesture mode** — index-finger tip is the pointer (direct, mirrored, like the
  tunneler); **pinch to select** the target under the cursor *instantly* (select
  on pinch-down, once per pinch — the tunneler's `handlePinch` model that felt
  great). No face tracking active.
- **Eye/Head mode** — the head (nose) is the pointer; **dwell to select** (hold
  the pointer on a target ~2–2.5s; a progress orb fills, then a satisfying
  **snap**). No hand needed, no pinch.

The mouse view is a third, trivial fallback: it's just the menu (click).

### 7.1.2 Tuning rules learned from live testing (bake these in)

- **Pinch must be SCALE-INVARIANT.** Normalize thumb–index distance by hand span
  (wrist→middle-MCP). Raw distance makes a far/small hand read as a constant
  pinch → false-positives that block everything. (Fixed 2026-07-18.)
- **Sticky hover.** Tolerate ~450ms of tracking jitter off a target before
  dropping it, or the dwell timer keeps resetting and never fires. (Fixed.)
- **Re-center + recalibrate after every selection.** Snap the pointer to the
  middle AND zero the head-pose origin to the user's current position, so the
  neutral pose maps to center and the user barely moves their head.
- **The mic is at center.** After re-centering the pointer rests on the mic —
  holding on it (dwell ~1s) **arms listening**; moving off stops and sends.
- **Finger spotlight.** Show a soft glow in the background at the detected finger
  position (tightens/brightens on pinch) so the user sees what's being tracked.
- **Transcript never covers the orbit.** The options ring is a full circle around
  center; float the transcript in whichever gutter has the most room (right on
  ultrawide, corner/top on portrait) — never bottom-center.

### 7.2 The scene
- **WebGL2**, Three.js. A **living companion form/orb** at center that reacts to
  state (idle / listening / thinking / speaking) and evolves with the conversation.
- **Light / bright by default**; brightens (a "mirror") while listening/speaking
  to **fill-light the user's face for the camera**.

### 7.3 Options as an even orbit
- The AI's offered choices render as **big portals evenly distributed around the
  center** — first at 12 o'clock, then 360°/N apart. Large, well-separated targets
  (Fitts's law for gaze + pinch). **Never crumpled to one side.**

### 7.4 Voice-first transcript
- Show only the **spoken line**; the full text hides behind a quiet disclosure.

### 7.5 Guided onboarding — the "First Interview"
- A **spotlight + coach-card + pulse-to-target** loop (adapted from the brainstem's
  First Interview at `localhost:7071 → startTour`) that **teaches the gesture loop
  end to end**: look-and-pinch the center to speak → choose a portal by gaze+pinch.
  It highlights exactly where to go next, through whatever modality.

### 7.6 Transport — demo shape == live shape
- The page **always `POST`s `/chat`** and reads `data.response`.
- **Response protocol** (the brainstem already speaks it):
  `{ response: "<full text>|||VOICE|||<spoken line>|||HOLO|||{prompt, options}" }`
  - `|||VOICE|||` → the spoken line (TTS + transcript).
  - `|||HOLO|||{ "prompt": "...", "options": [{label,value}] }` → the orbit portals.
- A **removable "static brainstem" shim** intercepts `fetch` and returns the
  identical shape from canned tour data, so the standalone demo needs no server.
  **Delete the shim, or pass `?server=<url>` → live, page unchanged.**

### 7.7 Privacy
- All vision (camera + MediaPipe) runs **locally in the browser**; the stream
  never leaves the machine. Say so in the UI.

## 8. Success criteria

- A first-time user, hands-free, completes a full turn — **look → pinch → hear the
  answer → pick a portal** — guided only by the First Interview, no other instruction.
- Gaze cursor is stable; pinch-select is reliable; **no mis-selects from jitter**.
- The demo runs with **no server**, and swaps to a live brainstem by deleting one block.

## 9. Aesthetic

Apple-grade minimal: thin-stroke SVG icons, **no emojis**, light/calm/premium,
very few controls. If a button existed on the old keypad, that is not a reason to
keep it.

## 10. References (the quality bar)

- **NexusWorlds** — immersive Three.js world, glowing emissive companion orb,
  shader portals you travel into. Aesthetic + spatial-navigation north star.
- **Cumulative 3D Dimensional Visualizer** (`iframe-tunneler-10.html`, despite the
  name has no iframes) — a central form that **mutates and accumulates**.
- **Brainstem First Interview** — the guided teaching loop to mirror.

## 11. Tech

Single self-contained HTML. Three.js r128+ (WebGL2). MediaPipe `tasks-vision`
(face + hand landmarkers). Web Speech API (STT/TTS).

## 12. Milestones

1. **M1 — Scene**: companion orb + light theme. Get it *beautiful*, alone.
2. **M2 — Gesture loop**: gaze cursor + pinch select, tuned until effortless. ← the bar
3. **M3 — Voice**: STT/TTS + barge-in.
4. **M4 — Orbit + transport**: even orbit options + `/chat` + static demo shim.
5. **M5 — First Interview**: guided teaching loop.
6. **M6 — Ship**: as the flight's `/vui` on `feature/voice-gesturepad`.

## 13. Process (so it doesn't become a turd)

**Change one thing → screenshot → judge → next. Never batch blind.** The gesture
feel and the look can only be tuned with a live camera + visual loop. Start with
M1 and don't move on until it's genuinely good.
