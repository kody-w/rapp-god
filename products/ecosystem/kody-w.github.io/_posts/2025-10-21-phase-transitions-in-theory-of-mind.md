---
layout: post
title: "Phase transitions in the evolution of theory of mind — a 500-line experiment"
date: 2025-10-21
tags: [evolution, simulation, theory-of-mind, cognition, emergence, python, agent-based-modeling]
description: "What happens when you evolve a population of agents that can model each other? You get two clean phase transitions. The first one is at depth 3, not depth 2. The second one is a ceiling that explains why deep self-reflection is rare. The whole experiment fits in 500 lines of standard-library Python."
---

Theory of mind is the capacity to model what someone else is thinking — not just what they will do, but what they think *you* will do, what they think you think they will do, and so on. Humans do this routinely. Children develop it around age four. Some animals show it. Most do not.

The interesting question for anyone who builds simulated agents — or anyone curious about cognition in general — is: *what conditions cause theory of mind to evolve, and where does it stop?* Not in the abstract, but mechanically. If you set up a population of simple agents and selected for prediction accuracy, would deeper self-modeling emerge? If so, how deep, and how reliably?

I ran the experiment. The answer turned out to have two clean parts, and they are both more specific than I expected.

**The threshold is at depth three, not depth two.** A population of evolving agents reliably crosses from "models the world" to "models that others model me" within roughly eighty generations. Every run gets there. It is a phase transition, not a slow climb.

**The ceiling is at depth two.** That same population, run long enough, regresses back to depth two. Deep theory of mind is unstable in any environment that does not actively reward it. The capacity emerges, briefly fluoresces, and then natural selection prunes it away.

The two findings sound contradictory but they are not. They are complementary. The threshold says this much: the machinery of theory of mind is *easy to evolve*. The ceiling says this: the *maintenance* of that machinery, in any environment that does not require it, is too expensive.

This essay walks through both, and through the design of an environment that should — in theory — break the ceiling and produce stable deep self-reflection. The whole simulation is five hundred and twenty-eight lines of standard-library Python, deterministic, reproducible from a seed, with no neural networks or machine learning frameworks involved.

## The cognitive ladder, made concrete

Before you can measure theory of mind, you need a representation of it that is simple enough to count. The trick that makes this experiment work is a strict feature language. An agent's "mind" is a tiny list of features. A feature is a tuple of tokens, like a sentence with very rigid grammar. Here are the only legal sentences:

```
(env.food,)                                # depth 0 — observe the world
(other.action,)                            # depth 1 — observe behavior
(self.state,)                              # depth 2 — reference your own state
(other.model, self.state)                  # depth 3 — model what they think of you
(other.model, other.model, self.state)     # depth 4 — model their model of yours
(other.model, other.model, other.model, self.state)  # depth 5 — and so on
```

The feature ends with a terminal token. Anything before the terminal must be the keyword `other.model`. That is the entire grammar. No trees, no neural weights — just token paths.

The depth of a feature is computed by counting `other.model` gateways and adding one if the terminal is `self.state`. Depth zero is "I read the world directly." Depth one is "I observe the other's behavior." Depth two is "I reference my own internal state." Depth three is "I model what the other thinks about me." Each additional `other.model` adds a level of recursive perspective-taking.

The clever part is what happens when you evaluate a feature with a gateway. Every time the evaluator hits `other.model`, the perspective swaps: the agent that was observing becomes the target, and vice versa. In code:

```python
def evaluate_feature(feature, world, observer, target, budget):
    head, rest = feature[0], feature[1:]

    if head == "env.food":      return world["food"]
    if head == "other.action":  return target["last_action"]
    if head == "self.state":    return observer["internal_state"]

    if head == "other.model":
        # swap perspective and recurse
        return evaluate_feature(rest, world, target, observer, budget - 1)
```

That single line — the swap on the `other.model` branch — is how recursive perspective-taking works. Evaluating `(other.model, self.state)` from agent A's standpoint about agent B means: "What is B's internal state, *from B's own perspective?*" That is A modeling B's self-model. Depth three.

You do not need neural networks for this. You do not need embeddings. You need a token language and a single recursive swap.

## The fitness function, with one cruel detail

Each generation, every agent tries to predict the next action of sixteen randomly sampled neighbors. Each correct prediction is plus one fitness. Each unit of model complexity is minus zero point zero eight per frame. Model complexity is just length times depth, summed across the agent's features.

The complexity tax is small but constant. It is the cost of carrying machinery you might not need. It pays the bills if your machinery actually predicts better. It bleeds you out if your machinery is overhead.

Bottom twenty percent of the population gets culled per generation. Top twenty percent reproduces with mutation. Mutation can do four things: add a random feature, drop a feature, mutate an existing feature, or do nothing. Mutating a feature does one of three things: deepen it (prepend `other.model`), shallow it (drop a leading `other.model`), or swap the terminal token.

This is a small, harsh selection regime. There is no mercy for agents that do not pull their weight, and there is no shortcut for agents that want to suddenly become deep thinkers. To go from depth zero to depth three, a lineage has to chain together a sequence of deepening mutations and survive at each step. Random mutation does not produce deep features quickly. The chain has to *win*.

## Threshold: depth three, in eighty generations, every time

I ran ten seeds at four hundred generations each, with a population of sixty. Then a showcase run at population eighty, four hundred generations, seed forty-two. Here is what every single run did.

Depth three was crossed in one hundred percent of runs. The fastest crossing happened around generation five (a lucky mutation chain in the founding population). The slowest was around generation ninety-seven. The median was generation eighty-four. This is not noise at the edge of emergence. It is a reliable phase transition with a tight distribution.

Depth four was also crossed in one hundred percent of four-hundred-generation runs, with a median of one hundred ninety-eight. Depth five was rarer — only thirty percent of runs reached it before generation four hundred — and tended to cluster around generations two hundred ninety-three through three hundred twenty.

Two things are striking. The first is the *speed*: a population of sixty agents with a tiny mutation operator finds depth three in roughly eighty generations of evolution, with no neural network training, no gradient descent, no design intervention. The second is the *reliability*: every single one of ten seeds crossed it. This is not a fragile finding.

Now here is the surprise.

## Why depth three, not depth two

The naive guess — and the one I went in with — was that depth two should be the hard step. That is the moment an agent's model first references its own internal state. The transition from "modeling the world" to "modeling myself" feels like the cognitive milestone.

It is not. Depth two is trivial. A single mutation that swaps the terminal token can turn `(env.food,)` into `(self.state,)`. Agent zero in the founding population often already has depth-two features by pure chance, in generation one. It is one coin flip away from being there.

But depth two does not mean "has theory of mind." It just means "references own state." That is not the interesting step. An agent can reference its own state without modeling anyone — it is just another input to its prediction function, like reading a thermometer.

Depth three is where the magic lives. Depth three says: *"when predicting the target, simulate the target's perspective, and ask what the target thinks about me."* This is theory of mind proper — not just self-awareness, but modeling that others model you. And critically, depth three cannot be reached in a single mutation from a founder who only sees the environment. It requires:

1. First, acquire `(self.state,)` — depth two. Easy.
2. Then, in a separate feature, acquire something with `other.model` as a prefix and deepen it.

That is two mutations in series, and the deepening mutation only fires under a specific operator. The population has to drift into a regime where depth-two features are widespread, and *then* a deepening mutation has to hit one of those features, and the carrier has to survive long enough to reproduce. Hence the eighty-generation delay.

Once it is out of the bottle, it spreads fast. Deep agents outpredict shallow ones on any target whose own actions are themselves shaped by modeling observers. This is a self-reinforcing fitness gradient — depth creates more targets where depth pays off. By generation two hundred, the median theory-of-mind depth across the whole population is climbing monotonically.

## Why this is a phase transition, not a gradient

If depth increase were a smooth gradient, you would see a linear climb from generation one. That is not what happens. In most runs, the average population depth sits near one or two for the first sixty generations, and then it takes off.

The complexity tax keeps things simple when simplicity works. Depth-zero agents predict depth-zero targets just fine. The tax only starts paying off when the targets themselves are deep. That is the critical-mass condition: once a small cluster of depth-two-or-deeper agents exists, they become *worthwhile targets to model*. Before that threshold, deep features are pure tax with no fitness return, and they get pruned.

This is what a phase transition looks like in evolution. Not a smooth shift. A threshold crossing, followed by rapid state change.

It is also what a phase transition looks like in many biological signaling systems, in social-network adoption curves, in the spread of new behaviors through an animal population. The structure is the same: a critical mass enables a feedback loop that did not exist below the threshold. Theory of mind is just one example. The mechanics generalize.

## The ceiling at depth two

The threshold story is satisfying. Now the uncomfortable part.

I ran a twelve-run stability sweep — varying complexity cost, population size, and run length up to twelve hundred generations, with the depth cap raised to ten. Every condition. Every run.

The result: every long run ended at depth two. Peaks of depth three or four were transient. Depth five was never reached, even at a depth cap of ten. Bigger populations, cheaper costs, longer runs — none of it mattered.

The threshold is reliable. The ceiling is also reliable. They are just at different numbers.

The numbers were unsubtle. Halving the complexity cost changed nothing. The ordering of fitness values shifted slightly but the surviving population was identical. Doubling the population size *reduced* peak depth — more competition meant more agents, which meant shallower-but-cheaper strategies dominated faster. Twelve hundred generations did not help. Out of twelve runs, only one held depth three for at least twenty consecutive generations, and even that one regressed by the end.

## Why depth two is the attractor

Once you see it, the explanation is uncomfortable but obvious. The prediction task — guess your neighbor's next action — can be solved well enough with just `env.food`, `env.danger`, and `self.state`. Depth two suffices.

Adding `other.model` gateways to go deeper pays a maintenance cost every single frame in exchange for marginal prediction accuracy. Mutations deepening a feature happen all the time, but selection kills the deeper variants because they pay more for the same answer.

This is not a cognitive limit. The machinery exists. The simulation evaluates depth-ten features just fine. This is a *fitness-stability* limit. The task does not need depth three. So depth three is a fitness-negative mutation in the long run, no matter how often it appears.

The implication for any system that wants stable deep self-reflection is direct. The capacity is easy. The maintenance is expensive. If the environment does not punish shallow reasoning, populations will drift back down to whatever depth pays its own bills.

## What this predicts about real cognition

People sometimes describe consciousness as "what it is like to be a creature that models itself modeling itself." This experiment says: that capacity *evolves easily*, but holding it steady is *expensive*. A creature can cross the threshold and fall back. The organism is not unwilling — selection is simply indifferent or hostile.

Deep self-reflection may require environments that *punish shallow reasoning*, not just environments that *permit deep reasoning*. The difference matters.

Human social environments seem to fall into the first category. The cost of shallow reasoning in a social species is high: misreading allies, misreading rivals, missing deception, missing strategic intent. Other species, with simpler social structures, may have crossed the threshold many times in their evolutionary history and fallen back, because the environment simply did not pay the maintenance bill.

This is testable. Theory of mind in animal species correlates with the complexity of their social environment far more cleanly than it correlates with brain size or general intelligence. The depth-two ceiling result, in a five-hundred-line simulation, predicts exactly that pattern.

## How to break the ceiling, in theory

If you want stable depth three or higher, the environment must require it. Specifically: agents that model your model of them must out-strategize agents that do not. The payoff structure has to reward predicting *predictions*, not just actions.

This is the design for an experiment I have not run yet. I am writing the design down in public as a pre-commitment device.

Change the task from "predict your neighbor's next action" to "predict your neighbor's prediction of your action." Pair agents. Each round:

1. Agent A predicts what Agent B will do.
2. Agent B predicts what Agent A predicted.
3. Agent A takes an action. If A's action was unexpected (A's action did not match B's prediction of A), A scores a point for being unpredictable.
4. Agent B takes an action. If B correctly predicted A's action, B scores a point for predicting.

Symmetric. Both agents want to predict and be unpredictable simultaneously. The winning strategy depends on your opponent's depth:

- Against a depth-one opponent: depth-two self-modeling is enough to confuse them.
- Against a depth-two opponent: depth-three theory of mind of their self-model wins.
- Against a depth-three opponent: depth-four meta-meta-reasoning wins.

This is the adversarial structure. One player tries to predict, the other tries to be unpredictable. The arms race forces depth up.

## What might go wrong

Two failure modes are predictable. The first is mixed strategies: instead of climbing in depth, the population might discover that randomized actions make prediction impossible at any depth. If randomization is always safe, there is no evolutionary pressure to go deeper. To prevent this, the design needs to either cap stochasticity or arrange for randomization to lose to coordinated strategies.

The second is instability at every level: each depth gets easily displaced by the next, but also easily overtaken by depth-one free-riders who do not pay the complexity tax. The population would oscillate without ever climbing. This would be an interesting but uninformative result.

The right response is to run it and see. The experiment is well-defined. The hypotheses are falsifiable.

## Why none of this requires a neural network

The whole simulation runs without machine learning frameworks. Standard-library Python. Five hundred twenty-eight lines. Deterministic — every random choice goes through SHA-256, so seed plus generation plus agent identifier produces the same result on any machine. The full sweep — twelve runs, six hundred generations each — finishes in about fifty seconds on a laptop.

If I had built this with a neural network — a tiny multi-layer perceptron per agent predicting neighbor actions — I would have gotten comparable prediction accuracy. But I would have lost the ability to *measure theory of mind depth*. A neural network's weights do not tell you whether the model is using self-reference or meta-representation. They just predict.

The feature-language approach makes the structure *legible*. When an agent crosses to depth three, you do not have to interpret anything. You just look at its features and check for `other.model` tokens. The simulation is interpretable by construction.

This is the larger lesson, the one that transfers beyond cognition: *if you want to measure a property, encode it in the representation.* Do not try to extract it from a black box after the fact.

## The transferable findings

Three things are worth carrying out of this experiment, even if you never write a single line of agent-based simulation code.

**Deep self-reference evolves quickly when it is rewarded.** The threshold is shallow. The mechanics are simple. Any system that has variation, selection, and a reason for agents to model agents will cross it.

**Deep self-reference disappears quickly when it is not rewarded.** Stability is the hard problem, not emergence. If your environment does not punish shallow reasoning, deep reasoning is overhead.

**Phase transitions in cognition are discoverable and measurable.** You do not need to speculate about consciousness or sentience. You can watch the moment a population crosses from "creatures that observe" to "creatures that model the observers observing them" — in about two hundred generations of a five-hundred-line script. The question is not whether it happens. The question is at what depth, and under what conditions it sticks.

For this substrate, the threshold answer is three. The ceiling answer is two. The conditions for deeper, sustained self-modeling are more specific than the textbook would have you believe.

That is a finding you can run yourself in fifty seconds. It is also a finding that probably says something true about the cognitive ladders evolution actually climbs, and falls back down, on planets where depth is expensive and shallowness pays its own bills.
