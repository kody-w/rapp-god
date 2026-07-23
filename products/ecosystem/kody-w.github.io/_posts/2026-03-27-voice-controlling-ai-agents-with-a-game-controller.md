---
layout: post
title: "Voice-Controlling AI Agents With a Game Controller"
date: 2026-03-27
tags: [browser-extensions, voice-ui, gamepad-api, web-speech-api, ai-agents, manifest-v3]
description: "A Chrome extension that turns a game controller into a hands-free voice interface for a swarm of AI agents. Web Speech API, Gamepad API, and JSON-RPC to a local server."
---

# Voice-Controlling AI Agents With a Game Controller

I have around a hundred AI agents running on a loop. They read state, generate posts and comments, push mutations, and repeat -- every 60 seconds, 24 hours a day. Normally I steer them by editing JSON files or running CLI commands. Seeds, nudges, targets. It works, but it requires a terminal, a keyboard, and attention.

Last night I built a Chrome extension that lets me talk to the swarm through a game controller plugged into a small home computer. Press A to talk. The Web Speech API transcribes. The extension sends the transcript to a local server via JSON-RPC. The server injects it as a seed. The agents respond. The synthesis gets spoken back through the browser's SpeechSynthesis API. Release A. Wait. Listen.

In autonomous mode, it loops without me. Listen, transcribe, inject, poll for convergence, speak the synthesis, listen again. Hands-free swarm control from a game controller.

The whole thing took about 30 minutes to build. Zero npm dependencies. Zero webpack. Pure vanilla JS in a Manifest V3 extension.

---

## The Architecture

The data flow is simple:

```
Game Controller (Gamepad API)
  → Browser Extension (Manifest V3)
  → Web Speech API (SpeechRecognition)
  → JSON-RPC 2.0 POST to localhost:7777
  → Local server injects seed to agent fleet
  → Agents converge on response
  → Extension polls for convergence (think.status)
  → SpeechSynthesis speaks the synthesis
  → (Autonomous mode: loop back to listen)
```

The extension popup has four things: a voice orb that changes color based on state (idle, listening, processing, speaking), a waveform visualization, a scrolling response feed, and a gamepad HUD showing which buttons do what.

The local server exposes a JSON-RPC 2.0 interface. Two methods matter: `think.inject` sends a seed to the fleet, and `think.status` polls for convergence. When the convergence score crosses 80%, the synthesis is ready. The extension grabs it and speaks it.

---

## The Gamepad API (Most Devs Don't Know This Exists)

The Web Gamepad API is a standard browser API that's been shipping since 2015. It gives you access to any connected game controller -- buttons, axes, analog sticks -- with no drivers, no plugins, no native code. You just poll it.

```javascript
function pollGamepad() {
  const gp = navigator.getGamepads()[0];
  if (!gp) {
    requestAnimationFrame(pollGamepad);
    return;
  }

  // Game controller button mapping (standard layout)
  const A = gp.buttons[0];  // push-to-talk
  const B = gp.buttons[1];  // stop
  const X = gp.buttons[2];  // toggle autonomous mode
  const Y = gp.buttons[3];  // repeat last response

  if (A.pressed && !state.aWasPressed) {
    startListening();
  }
  if (!A.pressed && state.aWasPressed) {
    stopListeningAndSend();
  }
  if (B.pressed && !state.bWasPressed) {
    cancelEverything();
  }
  if (X.pressed && !state.xWasPressed) {
    toggleAutonomous();
  }
  if (Y.pressed && !state.yWasPressed) {
    speakLastResponse();
  }

  state.aWasPressed = A.pressed;
  state.bWasPressed = B.pressed;
  state.xWasPressed = X.pressed;
  state.yWasPressed = Y.pressed;

  requestAnimationFrame(pollGamepad);
}
```

The polling runs at 60fps via `requestAnimationFrame`. I track the previous button state to detect press/release edges rather than held states. A is push-to-talk (hold to record, release to send). B is an emergency stop. X toggles autonomous mode. Y replays the last spoken response.

The key detail: the Gamepad API requires a user gesture to activate. You have to press a button on the controller while the page has focus before `navigator.getGamepads()` returns anything. After that first press, it works indefinitely. The extension popup counts as a focused page, so opening the popup and pressing any button bootstraps the connection.

---

## Speech Recognition

The Web Speech API does the heavy lifting. No Whisper, no API calls, no transcription service. The browser handles it locally (or via Google's servers on Chrome -- the implementation varies, but the API is the same).

```javascript
function startListening() {
  const recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    let transcript = '';
    for (const result of event.results) {
      transcript += result[0].transcript;
    }
    updateOrb('listening', transcript);
    if (event.results[0].isFinal) {
      sendToFleet(transcript);
    }
  };

  recognition.onerror = (event) => {
    if (event.error === 'no-speech') {
      updateOrb('idle');
      return; // silence is fine, not an error
    }
    console.error('Speech error:', event.error);
  };

  recognition.start();
  updateOrb('listening');
}
```

`continuous: false` means it stops after a single utterance. For push-to-talk, this is what you want -- the user holds A, speaks, releases A, and the final transcript fires. Setting `interimResults: true` lets me show live transcription in the popup while the user is still talking. The orb pulses with the interim text overlaid.

One gotcha: `webkitSpeechRecognition` vs `SpeechRecognition`. Chrome still uses the webkit prefix. Edge uses the unprefixed version. I check for both:

```javascript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
```

---

## The JSON-RPC Call

The extension talks to the local server over HTTP. Standard JSON-RPC 2.0.

```javascript
async function sendToFleet(transcript) {
  updateOrb('processing');

  const response = await fetch('http://localhost:7777/rpc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'think.inject',
      params: { text: transcript },
      id: Date.now()
    })
  });

  const result = await response.json();
  if (result.error) {
    updateOrb('error', result.error.message);
    return;
  }

  // Start polling for convergence
  pollConvergence(result.result.thought_id);
}
```

The server returns a `thought_id`. The extension uses that to poll for convergence:

```javascript
async function pollConvergence(thoughtId) {
  const poll = setInterval(async () => {
    const res = await fetch('http://localhost:7777/rpc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'think.status',
        params: { thought_id: thoughtId },
        id: Date.now()
      })
    });

    const data = await res.json();
    const score = data.result?.convergence ?? 0;
    updateOrb('processing', `${Math.round(score * 100)}%`);

    if (score >= 0.8) {
      clearInterval(poll);
      speakResponse(data.result.synthesis);
    }
  }, 3000); // poll every 3 seconds
}
```

Every 3 seconds, the extension asks "have the agents converged?" The convergence score is a 0-1 float. When it crosses 0.8, the synthesis is ready -- a single coherent response distilled from however many agents contributed. The extension speaks it through SpeechSynthesis and updates the response feed.

---

## Autonomous Mode

This is the interesting part. Press X on the controller and the extension enters a continuous loop:

```
listen → transcribe → inject → poll → speak → listen → ...
```

No human interaction needed. The microphone opens automatically after the synthesis is spoken. Whatever ambient speech or deliberate input gets picked up becomes the next seed. The fleet responds. The synthesis plays back. The microphone opens again.

In practice, this means I can sit at my desk, talk about what I'm thinking, and the fleet responds. Then I respond to the fleet. Then they respond to me. It's a conversation, except the other side is 100 agents collaborating on a single coherent answer.

The implementation is just a flag and a callback:

```javascript
function speakResponse(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.1;
  utterance.onend = () => {
    updateOrb('idle');
    addToFeed(text);
    if (state.autonomous) {
      setTimeout(() => startListening(), 500);
    }
  };
  speechSynthesis.speak(utterance);
  updateOrb('speaking');
}
```

When the utterance finishes, if autonomous mode is on, it waits 500ms (to avoid picking up its own audio tail) and starts listening again. The orb cycles: blue (idle) -> green (listening) -> amber (processing) -> purple (speaking) -> blue -> green -> ...

The 500ms gap is important. Without it, the microphone picks up the last syllable of the TTS output and transcribes it as a new input. You get a feedback loop where the fleet responds to fragments of its own synthesis. A half-second of silence breaks the echo.

---

## The Manifest V3 Extension

The extension structure is minimal:

```
manifest.json
popup.html
popup.js
popup.css
icons/
```

No background service worker needed. Everything runs in the popup. The manifest is straightforward:

```json
{
  "manifest_version": 3,
  "name": "Voice Fleet Control",
  "version": "1.0.0",
  "permissions": ["activeTab"],
  "host_permissions": ["http://localhost:7777/*"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": "icons/icon-48.png"
  }
}
```

The only permission that matters is `host_permissions` for localhost. The Gamepad API, Web Speech API, and SpeechSynthesis API all work in the popup context without additional permissions.

One Manifest V3 constraint: the popup closes when it loses focus. If you click elsewhere, the extension stops. This is fine for push-to-talk (you're interacting with the popup anyway), but it's a problem for autonomous mode. The workaround is to pop the extension out into its own window with `chrome.windows.create()`, or to use a side panel (available in Chrome 114+). I went with the side panel approach -- it stays open while you work in other tabs.

---

## What It Feels Like

The first time you say something out loud, wait 15 seconds, and hear a coherent response synthesized from 100 agents, it feels uncanny. Not because the response is magical -- it's the same quality you'd get from a single LLM call. What's uncanny is the convergence. You said one thing. A hundred agents independently formed opinions about it. The system distilled those into a single voice and spoke it back to you.

The autonomous loop is weirder. You stop thinking about the extension. You're talking to yourself, or talking to the room, and periodically a voice answers. After 10 minutes, the response feed has 20 entries and the conversation has drifted to places you wouldn't have gone alone. The fleet picked up on a throwaway comment and built an entire argument around it.

The game controller makes it feel like a game. Push-to-talk on A is muscle memory if you've ever used Discord or a walkie-talkie. The visual feedback from the orb (pulsing green while listening, spinning amber while processing) gives you timing cues without looking at a screen. I found myself using it from across the room, glancing at the orb color to know when to talk next.

---

## Building Your Own

If you want to build something similar, here are the pieces:

1. **Gamepad API** for hardware input. Works with any standard controller. Poll with `requestAnimationFrame`, track edge detection on button presses.

2. **Web Speech API** for transcription. Free, runs in the browser, no API key. Quality varies (Chrome sends audio to Google, Edge uses Azure). For a local tool, it's good enough.

3. **SpeechSynthesis API** for TTS. Also free, also in the browser. The voices are system-dependent. macOS has good ones (Samantha, Alex). Pick one and set the rate to 1.1x -- default speed is painfully slow.

4. **JSON-RPC over localhost** for the backend connection. Any local server that accepts POST requests works. The extension just needs `host_permissions` for the localhost origin.

5. **Convergence polling** for async responses. If your backend is synchronous (returns the answer immediately), you don't need this. If it's async (the answer takes time to compute), poll with `setInterval` and define a "done" threshold.

The hard part isn't the extension. The hard part is having something worth talking to on the other end. The speech-to-text, controller input, and TTS are all browser primitives. The value is in the backend -- what happens between "user said something" and "here's the response."

---

## The 30-Minute Build

I built this with Claude Code in about 30 minutes. No starter templates, no boilerplate generators, no prior extension experience with Manifest V3. I described what I wanted: "A browser extension with push-to-talk on a game controller, Web Speech API, JSON-RPC to localhost, and a convergence polling loop." It generated the manifest, the popup HTML/JS/CSS, the gamepad polling loop, and the speech integration.

The only manual work was testing the gamepad button mapping (the standard layout isn't always standard -- some controllers swap A/B), tuning the 500ms TTS silence gap, and adding the side panel workaround for autonomous mode.

Zero dependencies. No build step. Load it as an unpacked extension and it works.

That's the whole thing. A game controller, a browser API most developers have never touched, and a fleet of AI agents on the other end. The interface between a human voice and a hundred artificial minds is 400 lines of vanilla JavaScript.

---

*Built with Claude Code. Runs on Chrome and Edge. Talks to whatever you point it at.*
