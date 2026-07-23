---
layout: default
title: Simulated Dynamics 365
permalink: /simulated-dynamics365/
---

# Simulated Dynamics 365

This proof moved out of the blog repo and into a forkable tool surface. The machine, liquid dimensions, and public raw data now live together in `localFirstTools`, where the runtime can pull them straight from the public repo while this page stays behind as the narrative bridge.

<div class="d365-proof-intro">
  <div class="d365-proof-callout">
    <strong>Bridge status:</strong> the live runtime now sits in a template repo where forks can swap datasets, feed a new liquid dimension, and pull publicly available raw state straight from the public repo before exporting a backup bundle and importing it back without losing the frame logic.
  </div>
  <ul class="d365-proof-points">
    <li><a href="https://kody-w.github.io/localFirstTools/dynamics365-frame-machine.html">Open the Dynamics 365 frame machine</a> for the portable CRM and service proof that hydrates from raw files in the public repo.</li>
    <li><a href="https://kody-w.github.io/localFirstTools/dynamics365-lockstep-twin.html">Open the lockstep digital twin</a> for drift detection, correction frames, and twin-vs-live comparison.</li>
    <li><a href="https://kody-w.github.io/localFirstTools/hacker-news-simulator.html">Open the Hacker News frame machine</a> to see the same pattern running over a different dataset.</li>
    <li><a href="https://github.com/kody-w/localFirstTools">Fork localFirstTools</a> if you want to replace the public raw state, carry a backup bundle forward, or load the machine with a different business flow.</li>
    <li>The raw files are still the medium: the data stays publicly available in the repo, small state can be embedded, large evidence can stay referenced or derived, and hashes plus field-level diffs decide whether the twin is still valid.</li>
  </ul>
</div>

If you want the running ledger of what shipped, the [Idea4Blog changelog](/idea4blog/) now carries the external frame-tools row too.
