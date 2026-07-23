---
layout: post
title: "Dogfooding Yourself: Use Your Twins for Real Work"
date: 2026-04-18
tags: [dogfooding, twins, discipline, personal-tools]
---

The fastest way to discover what's wrong with a personal twin you've built is to make yourself use it for actual work. Not a demo. Not a screenshot for a blog post. Real work, in real conditions, where the twin is your only path to getting something done.

This sounds obvious. It is not obvious. The default mode of building personal tools is to build them, admire them, take a screenshot, ship a blog post, and then go back to using the original platform because the original platform is more polished. The twin sits there, theoretically functional, never actually load-bearing for anything that matters. After six months it bit-rots and gets archived.

Dogfooding is the antidote. The rule is: once a twin exists, the original platform becomes the secondary surface and the twin becomes the primary one. Use the twin for the real workflow. Notice every paper cut. Fix the paper cuts. Iterate until the twin is materially better than the original for your workflow.

What this discipline reveals, every time:

**The polish gaps are different than you assumed.** You think the missing feature is X. The user (you) discovers the missing feature is Y. The twin has X because X was easy. The twin lacks Y because Y was annoying. Y is what blocks daily use. You only learn this by hitting Y in the wild.

**The data shape is wrong in ways you can't see by inspection.** Reading your own data structure looks fine. Trying to query it for a real task reveals that the field you need is a string when it should be an array, or it's at the wrong level of nesting, or it's split across two files when it should be one. These problems do not surface until a real task forces a real query.

**The defaults matter more than the features.** The twin has fifteen features. You use three. The three you use need to be the defaults — front and center, one click away. The other twelve are dead weight that crowds the UI. Dogfooding tells you which three are the three.

**The friction is in the round-trip, not the action.** The action is fast. The round-trip — make a change in the twin, see it reflected, share it with someone, get feedback, make another change — is slow. The round-trip is what determines whether you actually keep using the twin. If the round-trip is twenty minutes, the twin loses to the platform's two-minute round-trip every time. If the round-trip is thirty seconds, the twin wins.

**The "would I pay $5/month for this?" test.** If you wouldn't, it's not done. If you would, it's done.

The flip side: dogfooding only works if you commit to it long enough to push through the awkward middle. The first few weeks of using a twin you built will feel worse than using the platform, even though the twin is yours and the platform isn't. This is not a sign that the twin is bad. It's a sign that the twin needs polish work, and polish work is exactly what dogfooding is supposed to surface.

Push through. Make a list of every paper cut you hit in week one. Fix them in week two. Make a new list in week three. By month three the twin is materially better than the platform for your specific workflow. After that, you don't go back.

A specific habit: when you hit friction in your twin, do not work around the friction in the moment. Note it, finish what you were doing, and then immediately fix the friction in the twin's code before you start your next task. This converts every friction event into a permanent improvement. After enough cycles, the twin has been shaped by your actual usage patterns, which is the only thing that produces a tool that fits your hand.

The twins worth building are the twins you actually use. Build them so you can use them. Use them until they are better than what they replaced. Then keep using them.
