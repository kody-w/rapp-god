---
layout: post
title: "CSS filter on a 3D wrap silently flattens backface-visibility"
date: 2026-04-26
tags: [engineering, css, 3d, transforms, debugging]
description: "A flip-card showed the front mirrored on flip instead of the back. Cause: filter on a preserve-3d ancestor is a CSS Transforms L2 grouping property. Once a group flattens, backface-visibility is a no-op."
---

The card was supposed to flip. A click toggled `.flipped`, the wrap rotated 180 degrees, the back face — with the QR code on it — was supposed to appear.

What appeared instead was the front of the card, mirrored. Backwards text. Pip in the wrong corner. Same content, just reversed.

## The structure

Standard CSS flip-card pattern. Wrap with `transform-style: preserve-3d`. Two faces inside, both `position: absolute; inset: 0`. The back has `transform: rotateY(180deg)` so it's pre-flipped, sitting against the inside of the wrap. Each face has `backface-visibility: hidden` so only the side facing the camera renders.

```css
.wrap {
  transform-style: preserve-3d;
  transform: perspective(1000px) rotateY(0);
  transition: transform .4s ease-out;
}
.wrap.flipped { transform: perspective(1000px) rotateY(180deg); }
.face {
  position: absolute; inset: 0;
  backface-visibility: hidden;
}
.back { transform: rotateY(180deg); }
```

Add `.flipped`, the wrap rotates 180, the front is now facing away (culled by backface-visibility), the back is now at 360 degrees (= 0, facing camera). It works in every demo.

It didn't work in mine.

## What was different

One line. The wrap had a drop-shadow filter:

```css
.wrap {
  transform-style: preserve-3d;
  transform: perspective(1000px) rotateY(0);
  filter: drop-shadow(0 12px 50px rgba(0,0,0,.7))      /* ← this */
          drop-shadow(0 0 30px rgba(255,200,80,.12));   /* ← this */
}
```

Without the filter: flip works.
With the filter: front renders mirrored on flip.

## What's actually happening

`filter` is a **grouping property** in [CSS Transforms Level 2 §6.1](https://www.w3.org/TR/css-transforms-2/#grouping-property-values). When you set a grouping property on an element that's part of a 3D rendering context, the browser is required to flatten that element's descendants into a 2D group.

The grouping properties that cause this:

- `opacity` < 1
- `filter` other than `none`
- `mask`, `mask-image`, `mask-border-source` other than `none`
- `clip-path`
- `mix-blend-mode` other than `normal`
- `isolation: isolate`
- `will-change` listing certain properties
- `overflow` other than `visible`

Each one of those creates a "rendering group" — the browser has to composite the element's children together as a 2D image before applying the effect. There's no other way to make a drop-shadow follow the alpha of layered content.

The flattening is irreversible inside that subtree. The faces inside my wrap stopped being 3D rectangles oriented in space. They became a 2D collage that gets rotated as a single image.

## Why backface-visibility silently dies

`backface-visibility: hidden` works by checking whether the face's normal vector is pointing toward or away from the camera. That check requires a real 3D normal, which requires the face to actually be a 3D object.

Inside a flattened group, the back face's `transform: rotateY(180deg)` becomes a 2D mirror — a horizontal flip of its rendered pixels. There's no normal vector. The browser can't tell which side is "back" because both faces are now coplanar 2D rectangles.

Once you flatten, every face faces the camera. So the browser falls back to paint order: later siblings paint on top of earlier ones. In my case, the back was later in DOM order, so it should have won.

Except — and this is the part that took longest to see — the back face's `rotateY(180deg)` got applied as a 2D mirror, then the wrap's `rotateY(180deg)` got applied as another 2D mirror. Two mirrors compose to identity. The back face's pixels are right-side up. The front face's pixels got mirrored once, by the wrap. So in paint order: front (mirrored) paints first, back (correct) paints over it. You should see the back.

But the back has a transparent border-radius mask and the visible content sits inside it. The front behind it has the same border-radius mask. They're co-planar. The pixels stack precisely. Whichever the browser chose to show in the actual GPU compositor is the one I saw — which on Chromium turned out to be the front.

The point isn't the exact paint-order outcome. The point is: once filter flattens the group, you don't have a flip-card anymore. You have two pieces of paper glued back-to-back, both face up.

## The fix

Move the filter off the 3D wrap.

Where do you put it? Two options:

**Option A — outer wrapper.** Wrap the wrap in a parent that hosts the filter. The parent is 2D, the wrap inside it is still in a 3D context relative to its own children:

```html
<div class="shadow-wrap">
  <div class="wrap">
    <div class="face front">…</div>
    <div class="face back">…</div>
  </div>
</div>
```

```css
.shadow-wrap { filter: drop-shadow(…); }
.wrap { transform-style: preserve-3d; transform: …; }
```

**Option B — push the filter to the leaves.** Each face is the leaf of the 3D hierarchy. Its content is already 2D. Putting filter on the face flattens the face's content (which doesn't matter, it's 2D) without affecting the wrap's 3D context:

```css
.face {
  position: absolute; inset: 0;
  backface-visibility: hidden;
  filter: drop-shadow(…);
}
```

I went with B because the existing parallax-tilt JS already wrote `--shadow-x` and `--shadow-y` custom properties on the wrap, and CSS custom properties inherit, so the per-face filter picks them up for free. No DOM change.

## How long this took to find

A while. Embarrassingly long, in retrospect. The bug looked like backface-visibility was broken — which is what you fix first, by trying every backface-visibility-related dance: vendor prefixes, `transform-style` on faces, explicit `translateZ(1px)` on each face to break z-fighting, swapping the back to render before the front in DOM order. None of it worked.

The thing is, none of those fixes can work, because backface-visibility wasn't broken. The 3D context was. There was no 3D for backface-visibility to evaluate.

## How to spot this faster next time

Three diagnostic questions, in order:

1. **Is the wrap actually rotating?** Open devtools, click flip, watch the computed `transform`. If it changes from `rotateY(0)` to `rotateY(180deg)` and you still see the front, you have a 3D context problem, not a transform problem.

2. **Does the wrap have any of the grouping properties?** Search the wrap's computed style for `filter`, `opacity`, `mask`, `clip-path`, `mix-blend-mode`, `isolation`, `will-change`, `overflow`. Any non-default value on the wrap (or any ancestor that's part of the same 3D context) is your suspect.

3. **Does removing the suspect fix it?** Comment out one grouping property at a time. If commenting out `filter` makes the flip work, you've found it. Then your job is to put the effect somewhere it can't flatten the 3D context — outer wrapper, or per-face leaves.

## The rule

**Inside a `transform-style: preserve-3d` subtree, do not set any grouping property on an element whose 3D children must remain in 3D space.**

This is the rule the spec encodes; it's just easier to internalize as a sentence than to look up the grouping-property list every time. The rule means: filter, opacity, mix-blend-mode, mask, clip-path, isolation — all of these are "I am willing to lose 3D inside me" markers. If you don't want to lose 3D inside that subtree, push the property out to a parent or down to a leaf.

The flip card is the canonical example, but the same trap applies to any 3D effect: card carousels, cube transitions, page-turn animations, parallax stacks. Anywhere `preserve-3d` matters, grouping properties are quietly explosive.

## Where the spec text lives

[CSS Transforms Level 2 §6.1 "Grouping property values"](https://www.w3.org/TR/css-transforms-2/#grouping-property-values) is the citation. It's three paragraphs and a list. Worth memorizing once.

The spec is older than the bug-finding folklore around it. There's no shortage of Stack Overflow threads ending in "wrap it in another div" without explaining why. The why is the grouping-property list.
