---
layout: post
title: "The poor man's API — why the clipboard is a better integration than the real one"
date: 2025-10-23
tags: [engineering, automation, integration, software-design, human-in-the-loop]
description: "When you have valuable state on one side and a platform you want to influence on the other, you do not need an API. You need an HTML page that reads your state, generates the right text, and gives the human one click to paste it. Better than the real thing."
---

At some point while building a system that produces a lot of state — frame snapshots, agent posts, proposals, code reviews, trending discussions, merge events — I realized I had no good way to push any of it into the platforms where humans actually spend time.

A discussion forum. A code-host's settings pages. A team chat. A marketing newsletter. The pattern is the same: you have valuable state on one side, and a platform you want to influence on the other, and there is no API you can legally and practically automate at two in the morning on a Tuesday.

So I built a different kind of integration. I call it the poor man's API. It turns out to be better than the real thing.

## The problem with real APIs

The traditional approach to cross-platform automation is: OAuth flow, API keys, webhook handlers, rate limit management, token refresh logic, error handling, credential rotation. For one popular discussion platform: register an app, get approved, handle the requests-per-window limit, avoid the content policy tripwires, maintain the bot account's reputation score so it does not get shadow-banned.

That is six weeks of work to post content that a human could paste in six seconds.

The deeper problem is that full automation removes judgment. A bot posts the same thing whether it is appropriate or not. It does not know that the community just had a drama event and today is the wrong day for a promotional post. It does not notice that the exact angle you planned is already a top comment on someone else's thread. Human judgment is not a bug to be automated away. It is the most valuable part of the interaction.

## The pattern: build a digital twin page

Instead of building an API integration, you build an HTML page that does three things:

1. **Reads your system's live state.** Via a public URL, a local JSON file, or any URL you control. The page fetches it on load, every time.

2. **Analyzes what actions would be valuable.** Looks at the current state and generates suggestions: which discussions are gaining momentum, which proposals need visibility, what kind of content would land well right now based on what the agents are doing.

3. **Generates the exact text for each action, with copy buttons.** Not summaries. Not links. The actual title and body, formatted for the target platform, ready to paste.

The human is the API. The browser is the integration layer. Copy-paste is the transport protocol.

This sounds almost embarrassingly simple. It is. That is the point.

## Three concrete examples

I built three of these pages while developing one project, and each one taught me something different about the pattern.

**Discussion-platform action queue.** This page reads the current state — frame number, active prompt, agent count, recent posts, trending proposals — and generates twelve discussion-platform actions: replies to existing threads, new posts for topics the agents are actively debating, settings adjustments, crossposts to related communities. Each action has a copy button for the title and a separate copy button for the body. A checklist tracks what has already been posted so you do not duplicate. The rationale section under each action explains why it is being suggested based on the current state.

**Repository twin page.** This one reads live data from a code-host's API — pull requests, issues, commits, repo settings — and shows the target repo as it exists right now. It then generates a settings action queue: update the description to match what the project has become, add these topic tags, set the website URL. It also generates merge commands for open pull requests and steering nudges to feed back into whatever process produced the state. The whole page is a mirror of a remote repository that also tells you what to do about it.

**Engagement engine.** This is the most sophisticated one. It fetches live state from a public URL and generates different post types depending on what is actually happening: a "hook" post when a milestone is hit, an "update" post when activity spikes, a "showcase" post when a new artifact ships, a "question" post when a debate is active. The content adapts to the moment. If you open the page and there is nothing interesting happening, it tells you that and suggests waiting.

## The code pattern

The basic structure of every digital twin page is the same four functions:

```javascript
// 1. Fetch your state
async function loadState() {
  const res = await fetch(
    'https://your-state-url.example/state/snapshot.json'
  );
  return res.json();
}

// 2. Analyze what's interesting right now
function analyze(state) {
  const frame = state.frames.at(-1);
  const actions = [];

  if (frame.merges > 3) {
    actions.push({
      type: 'build-update',
      priority: 'high',
      reason: `${frame.merges} PRs merged this frame`
    });
  }
  if (frame.top_proposal?.votes > 50) {
    actions.push({
      type: 'governance-post',
      priority: 'medium',
      reason: 'proposal gaining traction'
    });
  }
  return actions;
}

// 3. Generate platform-specific text from state
function generatePost(action, state) {
  const frame = state.frames.at(-1);
  if (action.type === 'build-update') {
    return {
      title: `Frame ${frame.number}: ${frame.merges} PRs merged, ${frame.new_posts} new posts`,
      body: `The agents have been busy. This frame:\n\n`
          + `- ${frame.merges} pull requests merged\n`
          + `- ${frame.new_posts} new discussions\n`
          + `- ${frame.top_topic} is the most active channel\n\n`
          + `Full state: https://github.com/you/repo`
    };
  }
}

// 4. Render with copy buttons
function renderAction(action, post) {
  return `
    <div class="action">
      <p class="reason">${action.reason}</p>
      <div class="field">
        ${post.title}
        <button onclick="navigator.clipboard.writeText('${post.title}')">Copy title</button>
      </div>
      <textarea id="body-${action.type}">${post.body}</textarea>
      <button onclick="navigator.clipboard.writeText(
        document.getElementById('body-${action.type}').value
      )">Copy body</button>
    </div>
  `;
}
```

That's the whole pattern. Fetch, analyze, generate, copy. No server. No authentication. No deployment pipeline. The page is a static HTML file served by GitHub Pages. The state it reads is a JSON file in a public repo. The "integration" is the user's clipboard.

## Why the Clipboard Is the Best API

The clipboard has properties that no real API has.

**Zero authentication.** Every platform accepts paste. No OAuth, no API keys, no app approval process, no rate limits. The clipboard works everywhere, always, for free.

**Human judgment in the loop.** Before the text reaches the target platform, a human reads it. They can decide "not now," "let me tweak the tone," "this is perfect," or "the situation changed while the page was loading and this is no longer relevant." That judgment is valuable. An API call cannot make it.

**Platform-native behavior.** When a human pastes into Reddit, it looks like a human posted. Because a human did post. The platform's trust signals, karma systems, and moderation heuristics all respond to it correctly. No bot flags, no shadow banning, no account suspension.

**No maintenance burden.** APIs break. Rate limits change. Terms of service update. OAuth tokens expire. A page that generates text and puts it in the clipboard has exactly one dependency: the clipboard API, which is a 20-year-old browser standard. It will work in 2035.

## The connection to long-running simulations

This is where it gets interesting. The digital twin page is not just a convenience tool for posting content. It is a node in a feedback loop.

The output of one round becomes the input to the next round. The world state is the organism. Each round mutates it forward. The interesting behavior emerges from accumulated mutations over time, not from any single round.

The digital twin page extends that loop beyond the repository:

```
Agent swarm produces state (round N)
  → Digital twin page reads state
  → Page generates suggested external posts
  → Human copies and pastes
  → External readers see the post, click through to the project
  → Some of them file issues, open PRs, star the repo
  → Those actions mutate the project state (round N+1 input)
  → Digital twin page generates DIFFERENT suggestions next round
  → Cycle continues
```

The page is a one-way valve that lets internal state flow into human platforms and lets human engagement flow back as project activity. The clipboard is the junction point. It is simple enough to be reliable and fast enough to keep up with the simulation's cadence.

And because the page reads live state, not cached state, it adapts to what just happened. If a breakthrough merge event happened this round, the page suggests celebrating it. If a proposal just crossed the voting threshold, the page suggests announcing it. The suggestions are always calibrated to the current moment, not a stale snapshot from yesterday.

## Scaling to any platform

The pattern generalizes completely. Anywhere a human can paste text, you can build a digital twin page for it.

**Code-host repo settings.** Fetch the repo's current metadata. Compare it to what the project has become based on recent activity. Generate the updated description, topic tags, and website URL. Put each one in a copy button. The human opens settings, pastes, saves.

**Team chat announcements.** Read your deployment state. When a new version ships, generate the announcement text for each channel — general gets the user-facing summary, engineering gets the technical details, the watercooler channel gets the fun stats. Copy, paste, done.

**Email newsletters.** Read your content state. Generate a newsletter draft based on what actually happened this week. Not a template with placeholders — actual sentences about actual events, pulled from your state files, formatted for your email platform's paste-in editor.

**Any CMS.** Most blog platforms and CMSes have a web editor that accepts pasted text. A digital twin page can generate publication-ready content for any of them, customized to the platform's tone and format.

The only requirements are that your state is readable as JSON and your target platform accepts paste. Both are almost universally true.

## The philosophical point

I want to push back on the instinct to automate everything fully. The poor man's API sounds like a compromise — "we could not build the real integration so we built this instead." That is not the right framing.

The human in the loop is not a missing piece of the automation. It is a feature. When I read the page's suggestion and decide to post it, I am doing something an API call cannot do: I am making a judgment about appropriateness, timing, and tone with full situational awareness. I know that the community had a moderation event last week and is a little raw. I know that today's developments had an especially interesting debate and this particular post will land well. I know the exact phrasing that will feel native rather than promotional.

The AI generates the options. The human selects and executes. That is not a limitation. That is the most efficient possible division of labor: the machine handles the tedious state-reading and text-generation work, the human handles the contextual judgment that machines do not have yet.

A lot of automation projects fail because they try to remove the human entirely and end up building something brittle and untrustworthy in the process. The poor man's API keeps the human in a lightweight but meaningful role. The result is more reliable than a bot, more efficient than doing everything manually, and more appropriate than either extreme.

The clipboard is the most universal API in computing. It predates every platform you want to integrate with and will outlast most of them. Stop underestimating it.
