---
layout: post
title: "Five Tones in Sixty Lines"
date: 2026-04-19
tags: [classifiers, nlp, rule-based, ml-lite, design]
---

A small text-classifier tool I built sorts any pasted text into one of five tones: **adversarial**, **reflective**, **prescriptive**, **narrative**, **technical**.

Total code: about sixty lines. No training data. No model. No API. Twenty keywords per class, a scorer, a tiebreaker.

It's about 75% accurate on my test set. That's worse than a fine-tuned BERT. It's better than a fine-tuned BERT on every axis that matters for this tool.

## The architecture

Each tone has a keyword list:

```js
const TONE_WORDS = {
  adversarial: ['wrong', 'broken', 'myth', 'fail', 'dead', 'lie', 'stupid', 'fraud', ...],
  reflective:  ['learned', 'realized', 'noticed', 'surprised', 'turns out', 'seems', ...],
  prescriptive:['should', 'must', 'need to', 'always', 'never', 'the rule is', ...],
  narrative:   ['then', 'after', 'before', 'when', 'suddenly', 'next', 'story', ...],
  technical:   ['function', 'api', 'buffer', 'latency', 'algorithm', 'endpoint', ...]
};
```

The scorer counts occurrences of each keyword in the lowercased text, adds up per class, picks the max. Tie-breakers use document shape (a README defaults to technical, a short input defaults to whatever matched first).

That's it. That's the classifier.

## Why it works

Three reasons rule-based beats ML for this kind of tool:

1. **The categories aren't learned from data; they're declared.** I *chose* these five tones because they map to the five seed templates. A trained model would give me the tones the data has, not the tones I need.

2. **Wrongness is fixable in thirty seconds.** When I found the classifier miscategorizing a polemic as "build" I opened the file, read nine lines of code, and moved `tone === 'adversarial'` one conditional earlier. An LLM's wrongness requires a prompt change, a re-eval, maybe a fine-tune. The feedback loop is ten times slower.

3. **The rules ARE the documentation.** View-source on the HTML, scroll to `TONE_WORDS`, and you know exactly how the tool thinks. It's the most honest kind of UI: the algorithm is the help text.

## Why it doesn't need to be more accurate

The classifier feeds into a template picker. The template picker feeds into a dropdown the user can override. Any one misclassification costs the user one click. That's the error budget.

When your error budget is "one click" instead of "dollars" or "trust", you can use a classifier that's honest about being rough. A 75% classifier with a one-click recovery path is better UX than a 92% classifier with no recovery path.

## The generalization

Most small-scale text classification tasks don't need ML. They need:

- A clear list of categories (declared, not discovered)
- ~20 high-signal keywords per category (five minutes of brainstorming)
- A weak tiebreaker (falls through to a default)
- A UI escape hatch (the user can override)

That's ~90% as accurate as a fine-tune for 1% of the effort. It's static. It's offline. It's inspectable.

The ML industry has trained a generation of developers to reach for a model before checking whether the problem is actually hard. For text tasks scoped to five categories with keyword-visible signals, it usually isn't. Sixty lines of if-statements and a dropdown get you there.

Ship the classifier. Ship the escape hatch. Don't ship the model.
