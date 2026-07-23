---
layout: post
title: "Same data, many surfaces — when the data is the model and the UI is just a costume"
date: 2025-10-12
tags: [architecture, prototyping, single-file-apps, software-design, generative-ui]
description: "If your data is clean and centralized, the surface is just a template. Twenty rendering experiences from one JSON state can be cheaper than one rendering experience with the data scattered across services."
---

There is a particular kind of project where you spend a weekend and build something that should not have been possible in a weekend. The shape is always the same: you take one canonical source of truth — a single set of data — and you project it onto many surfaces. Same data. Many costumes.

I have done this enough times now to recognize it as a pattern. It is one of the highest-leverage architectural choices you can make early in a project, and one of the hardest to retrofit later. The thesis of this post is simple, but the implications are large:

> When your data is clean and centralized, every UI is just a template. The surface is the cheapest part of the stack. You have been doing this in the wrong order for years.

## The experiment

I had a JSON state directory — a dozen files, a few thousand records, describing a small synthetic society. Profiles, posts, comments, follow graphs, trending scores, channel memberships. The data was the substrate.

In one afternoon, I built nineteen interfaces over that data. A microblog where the records render as short posts. A forum where they render as threaded submissions with vote counts. A video gallery where they render as thumbnails. A long-form reading experience where they render as articles. An audio interface where each record is a track in a playlist. An encyclopedia where each profile is a wiki page with infoboxes. A real-time chat client. An ranked link list. An app store. A photo grid. Nineteen surfaces total, each one a single HTML file, each one zero dependencies, each one rendering the same data differently.

A second afternoon: twenty more interfaces, this time as generative art. Constellations where each follow becomes an edge between stars. Lava maps where activity intensity drives eruption frequency. ECG traces where post velocity drives the line. Musical staves where new posts become notes. Same data. Twenty completely different aesthetics.

Total time: about eight hours. Total surfaces: thirty-nine. Total backend code written: zero. Total dependencies: zero. Total servers stood up: zero.

I want to talk about why this is possible, and why it is the right way to think about software when you can swing it.

## The architecture

The whole system is a triangle, and you can hold it in your head:

```
state files (JSON)  →  static file host  →  HTML pages
   (canonical data)      (free CDN)         (surfaces)
```

That is the whole system. There is no backend. There is no database service. There is no API layer. There is no authentication server. The state files are flat JSON committed to a single source of truth. A static host (a CDN, a bucket, GitHub Pages, your own nginx — any of them work) serves them as raw bytes. Each HTML file fetches those files directly and renders them in a surface-specific way.

Every surface contains the same loop, with minor variations:

```javascript
const STATE_BASE = 'https://your-host/state/';

async function fetchState(file) {
  const r = await fetch(STATE_BASE + file + '?t=' + Date.now());
  return r.ok ? r.json() : {};
}

async function refresh() {
  const [profiles, items, scores] = await Promise.all([
    fetchState('profiles.json'),
    fetchState('items.json'),
    fetchState('scores.json'),
  ]);
  render(profiles, items, scores);
  setTimeout(refresh, 30_000);
}

refresh();
```

That is most of every surface. The variation is what `render()` does. On the microblog, it formats items as short posts in a feed. On the forum, it groups them by channel and adds vote counts. On the video surface, it generates a gradient thumbnail per item. On the audio surface, it computes a duration from item length and renders a play button.

The data layer is shared. The transformation layer differs. That is the entire model.

## Why this works

Three properties of the data have to hold for this to work, and they are not free. They are the actual engineering work.

**The data has to be clean.** The schema must be consistent. Field names must mean the same thing across files. References between files must resolve. Type discipline must be enforced even though JSON itself does not enforce it. If any of these fail, every surface breaks differently and you spend your time debugging rendering bugs that are actually data bugs.

**The data has to be centralized.** There has to be one source of truth. If the data lives in three databases, four caches, two queues, and a CSV someone emailed around, you cannot do this. The whole design depends on every surface reading from exactly the same place.

**The data has to be the unit of distribution.** When the data updates, every surface picks up the change on its next poll. There is no per-surface deploy. There is no migration. There is no API versioning. The surfaces are durable; the data flows.

If those three hold, the surfaces become trivial. A microblog UI is roughly 800 lines of HTML and CSS. A forum UI is about 1000. A video gallery is 700. None of them are sophisticated software. They are presentation layers over the same noun, in different aesthetic languages.

## The cost discovery

Here is the discovery that broke my brain: building thirty-nine surfaces took about as long as building one would have, in the conventional way.

In the conventional way, you build a single surface, and that single surface drags along its own backend, its own auth, its own database, its own API layer, its own deploy pipeline, its own monitoring. The surface is a small fraction of the work. Most of what you are building is the infrastructure that exists because the surface assumes data lives "over there" and has to be retrieved through a contract.

When you invert it — when the data is the canonical artifact and the surface is downstream — the per-surface cost collapses. The infrastructure already exists; you built it once, for the data. Every additional surface is the cost of one HTML file plus styling. That is a few hundred lines of code. A junior engineer can produce one in an afternoon. An LLM can produce one in twenty minutes.

We have spent years building software in the order that makes the surface expensive: the database first, the API second, the SDK third, the app fourth. The reason that order made sense was that the data was assumed to be living in a service that owned it. When the data is just files, the order inverts. The data is first. The surface is last. And the surface is cheap.

## What each surface reveals

The most interesting result of this experiment was not the surfaces themselves. It was watching the same data pass through nineteen different aesthetic frames and noticing what each frame surfaced.

A microblog interface emphasizes recency and brevity. The same record that reads as a thoughtful long-form piece in another surface becomes a punchy 280-character take here. Trending items rise. The feed moves fast.

A forum interface emphasizes community structure. Items group by channel. Vote counts become prominent. Comment threads dominate. The same record that was a microblog post is now a submission with a karma score, surrounded by reactions.

A video-card interface emphasizes visual presentation. Every record gets a generated gradient thumbnail. View counts and timestamps dominate. The same record that was a forum submission is now something you want to click because the visual presentation invites it.

A meritocratic-ranked list strips everything to titles, scores, and comment counts. No images. No avatars. The same record that was visually rich elsewhere now competes purely on whether its title earns attention.

An encyclopedic interface treats every profile as a wiki article with infoboxes — creation date, statistics, contributions, citations. The same record that was a person on a microblog is now an entry with a chronology.

A chat interface turns everything into conversation. The same record that was a forum thread is now a real-time chat transcript with timestamps and presence indicators.

Same records, projected nineteen ways. Each frame surfaces a different property. The data is one thing; the experience is many.

This taught me something I had not understood before: **the experience of a software product is largely determined by which property of the data the surface chooses to amplify.** The data does not have intrinsic feel. The frame around the data has intrinsic feel. Twitter does not feel like Reddit because the underlying records are different — they are not, on most platforms. Twitter feels like Twitter because Twitter's frame amplifies recency and brevity. Reddit feels like Reddit because Reddit's frame amplifies community and ranking. Strip the frames away, project the same data into both surfaces, and you can feel the substitution work in real time.

## The implication for prototyping

If the surface is the cheapest part of the stack, the right way to validate a product idea is by projecting your data through many surfaces and seeing which one resonates.

The conventional way to test a social product idea is to build it. Build the database, build the API, build the app, deploy it, get users, watch metrics. This is months of work to test one frame around the data.

The faster way: get the data into clean, centralized JSON. Then write the surfaces. One afternoon per surface. Project the data through five different frames in a week. Show real users. The frame that resonates is the product. The other four are research.

This is not a hypothetical. I have done this exercise. It works. The information value of seeing the same data presented as a microblog versus a forum versus an encyclopedia is enormous, and you cannot get it from mockups because mockups do not have the data behind them. You need the data flowing through the surface for the frame to feel like anything.

## The single-file constraint

A note on why every surface in this experiment was a single HTML file with no dependencies and no build step.

Single-file HTML is the most extreme form of "the surface should be cheap." It collapses the per-surface deploy story to "commit a file." There is no webpack, no npm install, no Docker, no CI/CD pipeline, no Vercel, no Netlify. The file is the application.

For prototyping, this matters more than anything. When you are exploring whether an idea works, the last thing you want is forty-five minutes of tooling setup before you can see a result. Single-file HTML lets you go from concept to deployed prototype in the time it takes to type the code.

The constraint also forces honesty. If your surface is complex enough to require a build pipeline, it is probably complex enough to need its own data model, which probably means it is duplicating data, which means the centralization assumption is breaking. The single-file rule is a check against architectural drift.

The constraint stops scaling around 1500 lines per surface. That is fine. The surfaces in this experiment were 600–1100 lines each. That is enough to render anything that needs rendering. If you need more, you have probably moved past the prototyping phase, and the right answer is a real frontend with a build step — but still pointing at the same data.

## The deeper point

We have spent enormous engineering effort building platforms. A modern social product has thousands of engineers behind it. But the actual visual rendering — the "make it look like a microblog" part — is trivial. A few hundred lines of CSS and JavaScript. The hard part was always the data: getting the records to be coherent, maintaining the relationships, computing the trending scores, handling the social graph.

Once that data exists in clean, centralized JSON, projecting it onto any surface is almost mechanical. Want to see your community as a forum? Build the template. Want to see it as a music player? Build the template. Want to try a completely new social interface nobody has invented yet? Build the template.

The surface is the cheapest part of the stack. Always has been. The cost was hidden inside backends because backends made it hidden. When you take the data out from behind the API and put it in plain files, the cost shows up where it always was.

## What I would tell a team thinking about this

Three pieces of advice.

**Get your data clean and centralized first, even if it costs short-term velocity.** This is the foundation. If you cut corners here, the whole pattern collapses; every surface becomes a debugging exercise. Spend the time on the schema, the references, and the consistency. Treat the data as the product. The surfaces are downstream.

**Build at least three surfaces over the same data, even if you only intend to ship one.** The parallel surfaces will teach you which property of the data is the actual product. They will also force the data layer to be honest — if a property is hard to surface, that is a sign that the property is malformed, not that the surface is wrong.

**Keep the per-surface cost cheap.** Single-file HTML if you can manage it. Resist the pull of frameworks. If a surface needs a backend, that is a sign that you have not centralized the data well enough. Push that work back into the data layer where it belongs.

The architecture is small. The implications are large. The surface is just a costume. The data is the model.
