---
layout: post
title: "The One-Word Bug That Filtered Out Every Candidate Silently"
date: 2026-04-18
tags: [debugging, bugs, war-stories, schema-drift]
description: "Three autonomous ticks. Zero promotions. Eleven valid candidates on the record. The tracker read one field name wrong, and an empty string compared less than every timestamp in the universe."
---

My prompt-evolution experiment scheduled three automated ticks over two hours. Every tick logged the same message:

```
frame N: HELD (no proposals this frame)
```

Eleven valid `[PROMPT-v*]` discussions were published in that window. The tracker found zero. No error. No warning. No exception. Just a clean "nothing to see here" in three consecutive runs.

Here's what was wrong:

```python
def find_proposals(cache, since):
    candidates = []
    for d in cache["discussions"]:
        # bug: the cache canonicalizes createdAt to created_at
        ts = d.get("createdAt", "")        # always returns ""
        if ts < since:                      # "" < any string = True
            continue                        # silently skips every post
        ...
```

The GitHub GraphQL API returns `createdAt` in camelCase. The local cache scraper canonicalizes it to `created_at` in snake_case before writing. I wrote the tracker looking at the GraphQL response schema. The tracker was reading a field that no longer existed.

`d.get("createdAt", "")` returned `""`. `"" < "2026-04-18T18:00:00Z"` is `True`. Every candidate got filtered out by the "too old" check. The function returned an empty list. The caller logged "no proposals." Done.

## Why it was silent

Three properties of the bug combined to make it invisible:

**1. `dict.get()` swallows the missing key.** If I had written `d["createdAt"]` it would have raised `KeyError` immediately on the first discussion and I would have fixed it in two minutes. The defensive `.get(…, "")` hid the bug by making the failure mode "return a default" instead of "raise."

**2. Empty string string-compares as less than every non-empty ISO timestamp.** In Python, `"" < "2026"` is `True` because string comparison is lexicographic and the empty string is shorter than any other string in the Unicode sort order. So the filter didn't just "sometimes" skip posts. It skipped **100%** of posts. Always. Deterministically.

**3. The tracker's success condition is "find nothing."** If no valid candidates exist, the correct behavior is HELD (no promotion). The tracker was designed to tolerate dry runs. A filter that always-empties looks identical to an experiment that's simply not getting traction.

The combination meant the bug survived three production runs and looked like expected behavior.

## How I found it

Not by reading logs. The logs said what they were supposed to say.

I found it because I knew independently (from scrolling GitHub Discussions in the browser) that valid proposals existed. Then I ran the tracker locally in a worktree with print statements inserted, and discovered the candidate list was empty on the first `.get("createdAt")` call.

The fix is one line. I also fixed three related schema mismatches in the same file:

```python
# wrong         → right
d.get("createdAt")           → d.get("created_at")
d.get("reactions")           → d.get("upvotes"), d.get("downvotes")
d.get("comments")            → d.get("comment_count")
d.get("authorLogin")         → d.get("author_login")
```

All four were cases where I had consulted the GraphQL response shape when writing the tracker, instead of the actual cache file on disk.

## Three habits this bug cost me

**1. Stop defaulting to empty.** `dict.get("key")` returns `None` on miss. `None < "2026"` raises `TypeError` in Python 3. That would have been a loud failure. By writing `dict.get("key", "")` I traded a loud failure for a silent wrong answer. Any default value you pass to `.get()` is a silent-failure invitation unless the default is guaranteed to survive every downstream use.

**2. When you have a GraphQL response and a local cache, pick one schema and stick to it.** My cache file and the live API disagreed on seven field names. Every place I touch the data, I have to remember which shape I'm looking at. The correct move is either (a) canonicalize once at ingress and never look at the raw API shape again, or (b) never cache — always query. I was doing both, which is the worst option.

**3. Build a "why was this rejected" log at the filter layer, not the promotion layer.** My tracker logged "HELD: no proposals" at the outer frame level. A better log would have been per-candidate: `skipped #15745: createdAt="" < since="2026-04-18T16:00:00Z"`. The per-item rejection log would have shown the empty-string pattern immediately. Silent filters are almost always where the bug is.

## A general observation about ingestion pipelines

If your pipeline has these ingredients — an external API, a local cache, and a filter that can legitimately return nothing — you have everything you need for this exact bug to recur. The recipe:

1. API and cache disagree on one field name.
2. The filter reads the field with a defensive default.
3. The default value accidentally passes the filter condition for *every* input.
4. The "no results" state is a valid normal-operation outcome.

Every scraper-plus-downstream-processor I've built has hit a variant of this at least once. The fix is never in the filter logic — it's in the discipline of schema management at the cache boundary.

Today's debugging bill: one line of code changed, three autonomous frames wasted, one morning of staring at commit hashes wondering why my experiment was "held" when the agents were visibly producing output. Not the worst bug I've shipped, but right up there for "most educational per character of diff."
