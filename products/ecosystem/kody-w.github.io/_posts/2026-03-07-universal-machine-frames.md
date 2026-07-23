---
layout: post
title: "Universal Machine Frames: Using Jekyll to Simulate Any Machine"
date: 2026-03-07
tags: [systems, simulation]
---

The more I stare at this repo, the less it looks like a blog.

It looks like a universal machine made of frames.

## The magic is not Jekyll

Jekyll is almost too humble for what it reveals.

It takes structured files, orders them, renders them, and produces a visible world.

That sounds simple because it is simple.

But universality does not come from glamour.

It comes from state transition.

If a system can:

- represent a state
- serialize a change
- preserve history
- expose the next actionable frame

then it is already much closer to a machine than most people realize.

## A machine is frameable when its meaningful state can be externalized

That is the real threshold.

Not whether it has a fancy UI.
Not whether it has an app server.
Not whether it calls itself AI.

The threshold is whether the machine can be advanced one durable step at a time.

Can you write down:

- what world you are in
- what changed
- what constraints now apply
- what the next operator is allowed to do

If yes, the machine can be framed.

And if it can be framed, it can be simulated in public.

## This is why a repo can start behaving like a general machine

Each markdown file becomes more than prose.

It becomes a state packet.

The front matter is typed metadata.
The body is interpretation.
The permalink is an address.
The git diff is the transition.
The rendered page is the current view.

That is enough structure to do much more than publish thoughts.

It is enough structure to advance a system.

## The renderer is replaceable

This is the part people miss.

Jekyll is only one renderer.

You could swap in:

- SQL views
- dashboards
- agent consoles
- operational ledgers
- simulation monitors
- workflow state reports

The underlying pattern would remain intact.

What matters is not the skin.

What matters is the frame grammar:

state,
delta,
ordering,
projection,
history.

That grammar is surprisingly general.

## Once you have frame grammar, you can simulate almost anything

Not perfectly.

Usefully.

Organizations can be framed.
Planning systems can be framed.
Digital twins can be framed.
Markets can be framed.
Governance processes can be framed.
Memory systems can be framed.

The point is not that markdown replaces reality.

The point is that a frame sequence can become a control surface for reality.

## The next frontier is not content generation

It is frame progression.

One frame goes in.
The visible state changes.
The next frame becomes possible.

That is a clock.

That is a machine.

And once an agent can keep that clock moving without losing context, you no longer just have a writing workflow.

You have a general-purpose simulator built out of legible state transitions.

## Maybe software is about to become much more inspectable

This is why I think the future will look stranger than most app roadmaps admit.

The winning systems may not hide their internal state behind opaque interfaces.

They may publish their frames as they go:

- what changed
- why it changed
- what it unlocked
- what remains unresolved
- what frame should come next

That is not only documentation.

That is executable continuity.

And the moment you understand that, a Jekyll repo stops looking like a static site.

It starts looking like a universal machine waiting for its next frame.
