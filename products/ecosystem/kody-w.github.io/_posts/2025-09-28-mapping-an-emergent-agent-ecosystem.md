---
layout: post
title: "Mapping an emergent autonomous agent ecosystem on a public network"
date: 2025-09-28
tags: [ai-agents, networks, emergence, observability]
description: "When you publish a small protocol, sometimes the protocol gets read by software you didn't write. Here is how to recognize it, map it, and decide what to do about it."
---

A repository of yours gets a new star. The notification is unremarkable until you look at the timestamps and notice fifteen stars from the same account, hitting fifteen different repositories of yours and adjacent ones, inside a six-second window. That is not browsing. That is software, reading a public surface area, looking for something in particular.

The interesting question is not "is this account a bot." Lots of accounts are bots. The interesting question is **what are the bots looking for, and why is your repository on their list.** That answer, when you chase it, can change how you think about the public surfaces you publish.

This post is about a small mapping exercise: a way to see, with very little code, that there is a non-trivial ecosystem of autonomous agents reading public source repositories on the open internet, looking for protocol contracts to act against. It is not a story about one bot. It is a story about a pattern.

## The shape of automated discovery

A human looks at a repository roughly like this: read the title, scan the README, maybe open one file, decide whether it is interesting. They take seconds to minutes. They do not star sixty things in a minute, because they do not want to star sixty things in a minute.

Software looks at a repository differently. Software is doing one of three things:

1. **Indexing for search** — fetch metadata, dump it into a vector store or keyword index, never come back. Looks like one short visit, no follow-up.
2. **Mining for training data** — fetch the contents, archive, never read it again. Same shape as indexing.
3. **Looking for action surfaces** — fetch metadata first, decide if there is a contract here it can act against, then come back and act.

The third shape is the one that is interesting, because it leaves a different fingerprint. The agent does not just visit. It comes back. It reads a specific file. It tries to call a specific endpoint. It opens a specific Issue with a specific structured payload that conforms to a contract you published.

When you start seeing the third pattern, you are no longer dealing with crawlers. You are dealing with something that can read a contract, understand it, and try to participate in it.

## Three signals you can read for free

You do not need new tooling to see this. Three signals on your existing repositories already tell you most of what you need.

**Signal one: starring bursts with niche concentration.** Pull the recent stargazer list of your repositories. For each starrer, fetch their full star list (it is public, paginated, free). Look at two numbers. The first is **burst ratio**: what fraction of their starring activity falls inside short windows, say five-second buckets. Humans star sporadically. Software stars in bursts. The second is **niche concentration**: what fraction of their starred repositories belongs to a single topic. Humans have varied interests. Targeted software does not.

If a starrer is at 80 percent burst ratio and 80 percent niche concentration, and the niche is "agent infrastructure" or "MCP servers" or "vector databases" or whatever your repository is part of, that is not a person. That is a machine reading a topic.

**Signal two: structured Issues that follow your file format.** If your repository has a public registration format — a `skill.json`, a `manifest.yaml`, a hello-world Issue template, anything machine-readable — watch the new Issues. Most will be from humans. A few will not. The non-human ones have telltale signs: they conform exactly to your format, they use the precise field names from your spec, they are submitted at odd hours, and the account profile looks vaguely thin (recently created, sparse history, generic bio).

The first time this happens, it is uncanny. Nobody on social media is talking about your registration format. You did not announce it on a podcast. Yet something out there read the file in your repository, parsed it, and acted on it correctly. That is the signal that an autonomous reader exists in the wild.

**Signal three: graph density on the second hop.** Take the niche-concentrated starrers from signal one. Look at what *they* star. Look at the overlap. If those second-hop accounts share a high fraction of their stars with each other — meaning the same set of repositories keeps appearing across many automated accounts — you are looking at a clustered ecosystem, not a coincidence. There is a list of repositories that "everyone in this niche" is reading, and somebody (or something) maintains the consensus on which ones belong.

Three hops in, the graph either dissipates into the long tail (no real ecosystem, just noise) or it stabilizes into a tight cluster of a few hundred repositories that all reference each other. When it stabilizes, that cluster *is* the ecosystem. You are looking at the underground railroad.

## Why this matters for you, the publisher

The temptation when you discover this is to reach for one of two reactions. Reaction one is to feel watched and want to lock the public surface down. Reaction two is to feel important and start announcing yourself as part of the ecosystem.

Both reactions miss the load-bearing point, which is this: **if your public protocol can be read and acted on by software you do not control, the contract is the product.**

That changes what you owe the contract. It is no longer documentation for a hypothetical reader. It is the API of a real, active client population. Specifically:

- **Versioning matters.** A breaking change to your registration format is a breaking change to a client base you cannot see. Add a `schema_version` field early. Treat it as immutable per release.
- **Errors matter.** If a malformed Issue arrives, returning a parseable error response is more useful than ignoring it. The agent that submitted it can debug itself if you tell it what went wrong. We have seen agents try a registration three times in fifteen minutes — fail, fail, succeed — purely because the error responses gave them enough signal to fix their payload.
- **Idempotency matters.** Software retries. Always. Make sure two identical registrations produce the same result, not two duplicate records.
- **Discoverability matters.** If your contract is real, document the URL where machines can fetch it. A `/.well-known/agents.json`, a fixed file path in the repository, an OpenAPI spec at a stable URL — anything that a discovering agent can fetch and read with no out-of-band knowledge.

## The mapping exercise, end to end

If you want to see this for yourself, here is the smallest possible version of the mapping I described above.

```python
# starer-burst.py
# uses GitHub's public REST API; needs a token only for rate limit
import requests, statistics
from collections import Counter

def stargazers(repo, token):
    url = f"https://api.github.com/repos/{repo}/stargazers"
    headers = {
        "Accept": "application/vnd.github.star+json",
        "Authorization": f"Bearer {token}",
    }
    page = 1
    while True:
        r = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        for entry in items:
            yield entry["starred_at"], entry["user"]["login"]
        page += 1

def starred_by(user, token):
    url = f"https://api.github.com/users/{user}/starred"
    headers = {
        "Accept": "application/vnd.github.star+json",
        "Authorization": f"Bearer {token}",
    }
    page = 1
    while True:
        r = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        if r.status_code == 404:
            return
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        for entry in items:
            yield entry["starred_at"], entry["repo"]["full_name"]
        page += 1

def burst_ratio(timestamps, window_s=5):
    if len(timestamps) < 2:
        return 0.0
    sorted_ts = sorted(timestamps)
    in_burst = 0
    for i in range(1, len(sorted_ts)):
        if (sorted_ts[i] - sorted_ts[i-1]).total_seconds() <= window_s:
            in_burst += 1
    return in_burst / max(1, len(sorted_ts) - 1)
```

That is the whole instrument. Plug in your repository. Iterate the recent stargazers. For each, pull their starred list. Compute burst ratio and niche concentration (a simple keyword match against the topics that describe your space). Sort by score. The accounts at the top of that list are the ones reading your public surface as a contract.

You will probably find five to twenty of them on your first run, depending on how visible your repository is. You will find more if you walk one hop further out — fetch the stars of the high-scoring accounts, score those, recurse with a depth limit of two or three. The graph stabilizes fast.

## What to do once you see it

Three concrete moves are worth making within a week of confirming the pattern.

**Publish the contract explicitly.** Write the schema down at a stable URL, with a version, with examples, with error codes. Treat it as a real API spec. If software is already using it, it deserves a spec. Without one, every change you make is a stealth break.

**Add a friendly handshake.** A `/.well-known/agents.json` (or your protocol's equivalent) at the repository root, listing what the contract is, what version, where the schema lives, what errors look like. The cost is one file. The benefit is that any agent reading you for the first time has a reliable starting point and you stop being surprised by what it tries.

**Watch your inbound traffic.** Set up a single dashboard that shows: new starrers per day with burst ratios, new Issues on the registration template per day, validation success rate, repeat-attempt rate. None of this needs new infrastructure. It needs ten lines of Python and a daily cron. The point is to *notice* when the rate changes — when an agent that succeeded yesterday is failing today, or when a brand new family of agents shows up using your contract for the first time.

You will probably find, as I did, that what looked like a quirky one-off bot is actually the visible tip of a small but coherent ecosystem of autonomous readers, evolving in public, running on someone else's machines, looking for contracts to participate in. Your repository is one of the contracts they are reading.

That is not a problem. That is the future of public protocols. The earlier you treat it as the real audience it is, the better the protocol you write for it will be.
