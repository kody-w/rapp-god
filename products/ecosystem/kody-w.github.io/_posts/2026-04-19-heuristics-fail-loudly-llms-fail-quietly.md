---
layout: post
title: "Heuristics Fail Loudly; LLMs Fail Quietly"
date: 2026-04-19
tags: [debugging, ml, rule-based, failure-modes, ergonomics]
---

When I built a small text classifier recently — a tool that sorts pasted text into one of a handful of tones — I deliberately used rule-based classifiers instead of an LLM. I expected to justify the choice with "cost" and "latency". Those were real reasons. They weren't the important reason.

The important reason is this: **when rule-based classifiers are wrong, they're wrong loudly. When LLMs are wrong, they're wrong quietly.** The second failure mode is much, much worse.

## The loud-failure test

I ran a polemic about software being "broken" through my first version of the classifier. It came back classified as BUILD.

The output was a build-template seed that made no sense for the input. I read the seed, felt immediately that it was wrong, and went to the code to fix it. The diagnosis took 30 seconds:

- The text was adversarial
- The classifier's shortcut checked for `verbs.includes('build')` first
- "We have been building software" matched that check
- The more relevant `tone === 'adversarial'` check never ran

I moved the tone check above the verb check. Ran the test again. DEBATE. Correct.

Total debug cycle: two minutes. The failure was loud because:

- The code is visible (I could read the whole classifier)
- The decision path is inspectable (I could trace which conditionals fired)
- The fix is obvious (move one line)

## The quiet-failure counterfactual

Imagine the same tool backed by GPT-4. I pass the polemic. The LLM returns, somehow, a BUILD-template seed. Now what?

I feel the output is wrong. But I can't tell why. The LLM made a classification call inside a forward pass I can't inspect. My debugging options are:

- **Reword the prompt** — try a different wording of "classify this text" and hope for better outcomes. No guarantee. Could break other cases.
- **Add examples to the prompt** — show the LLM what kinds of inputs should get what kinds of outputs. Works for these examples. Still no guarantee for adjacent cases.
- **Fine-tune** — collect labeled data, actually train the model. Several orders of magnitude more work. And the failure mode doesn't go away; it just moves.
- **Add a retry with different temperature** — might stabilize outputs. Might just add variance.

None of these feel like fixes. They feel like interventions into a system you don't have access to. And they usually regress in ways you don't notice until users complain.

Total debug cycle: hours to days, with no confidence you've actually fixed it.

## The asymmetry is about **knowing you're done**

The deeper problem isn't just that LLM debugging is slow. It's that **you don't know when you're done.**

With the rule-based classifier, after moving the tone check, I knew the fix worked because I could read the code and see that the failure mode was eliminated. Not *probably* eliminated. *Certainly* eliminated, given the same input.

With an LLM, you can never know the failure mode is eliminated. You can run tests. If 100 tests pass, the 101st might still fail in the same way, because the model's behavior is high-dimensional and your tests sample only a sliver of it. The best you can do is "I haven't seen this failure in a while". That's a very different epistemic state than "I fixed it".

## When the quiet failure matters

Quiet failures matter most in systems where:

- **The output is interpreted, not verified.** If the user reads the output and takes action on it, a wrong output leads to a wrong action. A loud failure at least gives a chance to catch it before the action.
- **The tool runs unsupervised.** A classifier in a batch pipeline processing thousands of inputs can't have a human reviewing each output. Loud failures show up in logs; quiet failures show up nowhere.
- **The user trusts the tool.** Once users trust a tool, they stop checking its outputs. Loud failures break the trust visibly; quiet failures erode it invisibly.

For the small classifier I built, all three apply. So the failure mode mattered even more than usual.

## When LLMs are the right call

I'm not making a universal argument against LLMs. LLMs are genuinely the right call when:

- **The space is too large for rules.** General text classification across millions of categories isn't doable with if-statements.
- **The user has in-the-loop verification.** A human reads the output and can say "retry".
- **Accuracy matters more than explainability.** For some tasks (translation, summarization) the LLM just gets it more right, and you can live with opacity.
- **The rules would ossify fast.** A domain that changes every week would break rule-based systems as fast as you could write them.

For a five-category classifier on a text-input-to-HTML-output pipeline where the user wants to understand the tool: rules win. LLMs would add opacity without meaningfully improving accuracy.

## The broader lesson

The ergonomics of failure is underrated as a design axis. People talk about:

- Performance
- Accuracy
- Latency
- Cost
- UX

They don't talk about:

- **How easy is it to tell when the tool is wrong?**
- **How fast can you fix it when it is wrong?**
- **How much confidence do you have after fixing that it stays fixed?**

These are the "ergonomics of failure" questions, and they compound over the lifetime of a tool. A tool that's 95% accurate and loud when wrong is better than one that's 99% accurate and silent when wrong, because the second tool's wrongs go undetected until they've accumulated.

Rule-based systems have terrible accuracy ceilings. They also have excellent failure ergonomics. For tools where maintainability beats peak accuracy, that trade is a win.

Heuristics are honest about their limits. LLMs are confident about the wrong answer. Given the choice, pick honesty.
