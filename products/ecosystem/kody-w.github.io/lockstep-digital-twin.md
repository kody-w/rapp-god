---
layout: default
title: Lockstep Digital Twin
permalink: /lockstep-digital-twin/
---

# Lockstep Digital Twin

This proof builds the stricter version of the claim. Each accepted action is projected into the twin and sent against a mocked live Dynamics instance. Execution halts the moment the two disagree.

<div class="lockstep-proof-intro">
  <div class="lockstep-proof-callout">
    <strong>Operating rule:</strong> a digital twin only counts while the simulated state and the live state remain in lockstep. Drift is a failure condition, not a cosmetic detail.
  </div>
  <ul class="lockstep-proof-points">
    <li>Each action carries a twin projection and a live adapter response.</li>
    <li>Small state can be embedded while large evidence stays referenced or derived.</li>
    <li>Hashes and field-level diffs decide whether the twin is still valid.</li>
    <li>The console can step one action at a time or sprint until drift.</li>
  </ul>
</div>

<div id="lockstep-twin-app" class="lockstep-twin-app">
  <noscript>
    <p>This proof needs JavaScript enabled so the twin can execute and compare states.</p>
  </noscript>
</div>

<script src="/js/lockstep-twin-data.js"></script>
<script src="/js/lockstep-twin.js"></script>
