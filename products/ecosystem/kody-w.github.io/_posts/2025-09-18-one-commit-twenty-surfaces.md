---
layout: post
title: "Simulate the medium, not the audience"
date: 2025-09-18
tags: [engineering, architecture, publishing, broadcast]
description: "Posting to twenty platforms means twenty APIs, twenty rate limits, and twenty bans waiting to happen. There is a cheaper move — clone the shape of each platform inside one repo, and publish to all of them with a single commit."
---

Anyone who has tried to broadcast the same announcement to many places has discovered the same wall: every platform is a different API, with a different auth flow, a different rate limit, a different terms-of-service interpretation, and a different attitude toward bots. Cross-posting a launch to Twitter, LinkedIn, Hacker News, Reddit, Medium, Substack, Dev.to, and a half-dozen others is not a content problem. It is a plumbing problem that gets worse the more places you want to reach.

Most of the cost is accidental. The thing you are actually trying to do — *show the same announcement in twenty different formats* — is not difficult. The difficulty comes from doing it through the live platforms, where each one charges you in a different currency: tokens, OAuth dances, moderation queues, account suspensions.

This post is about a different move I have been running for a while: **simulate the medium instead of integrating with it**. Build twenty static pages in one repository, give each one the visual and structural shape of a real platform, write the announcement once, run a small script that translates it into each platform's native data shape, and `git push`. One commit, twenty surfaces, zero APIs touched.

It sounds like it shouldn't work. It works extremely well, and the reasons it works are worth writing down.

## Why APIs are the wrong place to hit

Pretend for a moment you do want to post the same news to twenty real platforms. Here is what you actually have to build:

- Twenty SDKs (or twenty hand-rolled HTTP clients, equally bad).
- Twenty auth schemes — OAuth with refresh tokens, API keys, signed-bearer tokens, login dances.
- Twenty rate-limit budgets to keep track of independently.
- Twenty different ToS interpretations on what counts as a bot.
- Twenty different content-policy regimes that can suspend you arbitrarily.
- Twenty different failure modes when something goes wrong.

I tried automating a single GitHub Discussion post recently and got rate-limited after two requests with a vague "submitted too quickly" error. Twitter's developer API costs at least $100/month for any meaningful posting volume. Reddit requires an OAuth handshake that includes a refresh-token rotation. Some platforms — Stack Overflow being the obvious one — explicitly forbid automated answers.

The accidental complexity of integrating with the live platforms is doing none of the work you actually wanted done. It is paying tax on the privilege of reaching real audiences who, for the kind of content I'm describing here, are mostly not looking at automated feeds anyway.

## What you actually want

Strip the problem down. What you want from a platform when you post to it is:

1. A native-looking presentation of your content (a tweet looks like a tweet, a Hacker News story looks like a story).
2. A reasonable archive (the post is still there next month).
3. A linkable URL.

That is it. The platform's ranking algorithm, its discovery mechanics, and its incidental audience are bonuses. They are also exactly the parts that fail you when you are publishing high-volume automated or AI-generated content — algorithms suppress it, discovery never picks it up, audiences don't engage.

The three things you actually want — native presentation, archive, URL — are nearly free to build yourself.

## Twenty surfaces in one repo

The setup I run looks like this. Inside one repository, there are twenty HTML files, one per platform shape. Each one is a single-page mimic of the visual structure of the real platform — a Twitter-style timeline, a Hacker News–style story list, a Reddit-style thread view, a wiki article page, a Substack-style newsletter layout, an Obsidian vault graph, and so on. None of them try to be the real thing pixel-for-pixel. Each one is unmistakably evocative of its inspiration.

Each HTML page does one thing on load: `fetch()` a JSON file from the same repo, parse it, render it. The HTML file is the renderer, the JSON file is the data. The visual style lives in CSS. None of this requires a build step or a framework — vanilla HTML, a few hundred lines of vanilla JavaScript per surface, GitHub Pages serving the lot.

The data files live alongside the renderers — one JSON file per surface, each shaped like that platform's native data:

- `twitter.json` is a list of tweets with `text`, `handle`, `likes`, `retweets`.
- `hackernews.json` is a list of stories with `title`, `url_domain`, `points`, `comments_count`.
- `wiki.json` is a list of articles with `article_title`, `body`, `editor`, `word_count`.
- `obsidian.json` is a list of atomic notes with `title`, `body`, `wikilinks`.
- … and so on, one shape per platform you care about.

The point is that each JSON file speaks the *language* of its platform. That is what makes the surface feel like the platform when you look at it, even though no real platform was touched.

## One announcement, twenty translations

The interesting code is the publisher. When I want to announce a new spec, a new release, a new piece of work, I write *one* canonical event — usually a couple of dictionaries: a title, a body paragraph, some tags, an optional URL. Then a single Python script does this:

```python
for surface, builder in BUILDERS.items():
    path = DATA_DIR / f"{surface}.json"
    data = json.loads(path.read_text())
    list_key = next(k for k, v in data.items() if isinstance(v, list))
    echo = builder(canonical_event)
    if any(e.get("id") == echo["id"] for e in data[list_key]):
        continue                          # idempotent
    data[list_key].append(echo)
    path.write_text(json.dumps(data, indent=2))
```

`BUILDERS` is a dictionary of small functions, one per surface. Each builder is ten to thirty lines: it takes the canonical event and produces a dictionary shaped like that platform's data. `twitter()` produces `{"text": ..., "handle": ..., "likes": 0}`. `hackernews()` produces `{"title": ..., "url_domain": ..., "points": 1}`. `wiki()` produces `{"article_title": ..., "body": ..., "editor": ..., "word_count": ...}`.

Each builder knows the medium. The loop does not. The loop just iterates, calls the builder, appends the result, and saves the file. Adding a new surface is one new HTML page, one new JSON file, one new builder function. Linear cost.

After the script finishes, `git add -A && git commit && git push` does the rest. GitHub Pages picks up the change in thirty to sixty seconds. All twenty surfaces show the announcement, each in its native format. No accounts. No API keys. No rate limits.

## The composite key that makes parallel writers safe

There is one detail in that builder pattern worth calling out, because it is what lets multiple machines (or multiple processes) write to the same surface without stepping on each other.

Every echo gets two fields that together act as a composite primary key:

```json
{
  "id": "echo-a8dcfaba",
  "frame": 530,
  "utc": "2026-04-17T22:00:00Z",
  "platform": "twitter",
  "text": "..."
}
```

`frame` is a monotonically increasing tick counter for the system. `utc` is the wall-clock time. Together, they uniquely identify the *event*, regardless of which surface it's being projected onto. The loop above checks for `id` collisions before appending, so re-running the publisher is a no-op. Two writers producing the same canonical event at the same `(frame, utc)` produce the same echoes; the second writer's append is detected as a duplicate and skipped.

This is the small piece of discipline that turns "twenty JSON files" into "twenty mergeable JSON files." Without it, a parallel writer is a corruption hazard. With it, the publisher is idempotent and safe.

## What you give up — honestly

It is worth being explicit about the one real thing you give up. The simulated surfaces have **no incidental audience**. Nobody who is browsing real Twitter sees your simulated tweet. Nobody on real Hacker News upvotes your simulated story. The only people who reach your surfaces are ones who already came to your domain. Every reader is intentional.

For some kinds of content, that is a fatal cost. If you are doing organic social marketing, you need the real platform's audience and discovery. Skip this whole pattern.

For the kind of content I'm describing — high-volume automated work, machine-generated artifacts, internal logs of an autonomous system, build status, agent output — the lack of incidental audience is fine, often preferable. The real platforms would suppress that content anyway. What you want is a native-looking, durable, linkable presentation of the work, and that is exactly what the simulated surfaces give you.

## What you gain — concretely

For the workloads where the trade is favorable, the gains stack quickly:

**Cost.** Real Twitter posting tier is $100/month minimum. Mailchimp for the Substack analog is another $30/month. Reddit, Discord, Slack — each one is its own subscription or workspace. The simulated version is free. GitHub Pages serves the HTML, `raw.githubusercontent.com` serves the JSON, edge caches make it fast.

**Scale.** Real APIs each have their own rate limit. Posting to twenty in parallel is twenty different rate-limit budgets to track. The simulated version is one `git push` per round of announcements, regardless of how many surfaces you have.

**Latency.** Each real-platform API call is a hundred to two thousand milliseconds. Twenty of them in sequence is twenty-plus seconds. One git push is two or three seconds, and GitHub Pages catches up in under a minute.

**Moderation.** A real platform can suspend your account at its sole discretion, and you have no recourse. The simulated surfaces are hosted in your repo. Nobody can take them down except you and your hosting provider.

**Archive.** Real platforms can and do delete content — sometimes whole accounts, sometimes specific posts. Git history preserves every echo file at every commit. You can `git checkout` any past state and see exactly what each surface looked like on a given day.

**Reproducibility.** Running the publisher with the same canonical event produces identical JSON across runs. Idempotent appends mean you can replay history. Good luck doing that against a real social platform's API.

## The deeper point

There is a more general pattern lurking under all this. *Most of the time, when you think you need to integrate with a system, you actually only need the system's surface.* The audience, the algorithm, the network effects of the real platform — those are real, and they are the parts the platform charges you (in tokens, in rate limits, in account-suspension risk) to access. The *shape* of the platform — what a tweet looks like, what a thread looks like, what an article looks like — is mostly free to reproduce.

Whenever you find yourself building twenty integrations to do twenty variations of the same content presentation, ask whether the integrations are doing useful work for you, or just charging you for the privilege of conforming to twenty different gatekeepers. If the latter, build the surfaces yourself. The cost is linear in surfaces, the result is owned, and you stop paying tax on plumbing.

For automated systems and AI-generated content in particular, the math is overwhelming. One commit. Twenty faces. Zero rate limits.
