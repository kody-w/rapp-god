---
layout: post
title: "Separate your runtime from your state — the migration pattern that lets you change engines without downtime"
date: 2025-10-16
tags: [architecture, devops, zero-downtime, software-design, migration-patterns]
description: "If your runtime and your state live in the same place, you cannot move one without disturbing the other. The fix is to put them in different places on purpose, even when one is hypothetical. Here is how."
---

There is a class of migration that is supposed to be impossible: moving the brain of a system from one place to another while the system is still running. You cannot stop the system. You cannot pause it. You cannot freeze its state and copy it. The system has to keep running while the engine moves underneath it.

I have done this twice. Both times, the technique was the same, and both times the technique was much simpler than the rumor of "zero-downtime migration" suggests.

The technique: **separate your runtime from your state, on purpose, before you need to.** When the two live in different places, moving one of them is straightforward. When they live in the same place, moving anything requires moving everything, and the whole point of the system has to pause.

This post is about the pattern, why most systems fail it, and how to retrofit it without rewriting your code.

## The two-path pattern

The insight is small enough to fit on a sticky note. **Every engine script needs to know two things, and only two:**

1. **Where am I?** The location of the engine — the code, the prompts, the rules, the orchestration.
2. **Where is the state?** The location of the data — the actual records the engine operates on.

If both answers come from the same source — the same directory, the same repository, the same database — moving either one means moving both. The two are entangled. You cannot redeploy the engine without touching the state, and you cannot relocate the state without touching the engine.

Make those two answers come from independent sources, and the entanglement disappears.

Concretely:

```python
# Where am I?  (resolved from the engine's own location)
ENGINE_ROOT = Path(__file__).resolve().parents[2]

# Where is the state?  (resolved from environment, with a sensible default)
STATE_PATH = Path(os.environ.get("STATE_PATH",
              str(Path.home() / "data" / "state")))
```

That is the entire pattern. Every script in the engine resolves its own location relative to itself, never relative to the state. Every script reads the state's location from a single environment variable. The two answers are independent.

Now, when you want to move the engine, you change `ENGINE_ROOT`'s actual location and update one variable in the launcher. The state is unaffected. When you want to move the state, you change `STATE_PATH` and start the engine pointing at the new location. The engine code is unaffected.

You can do both at once. You can do either. You can run two engines against the same state for an A/B comparison. You can swap the state to a snapshot for time-travel debugging. The decoupling unlocks everything.

## Why most systems fail this

Most systems entangle runtime and state because the entanglement is invisible at the start. When you build a small project, both naturally live in one place — one repository, one directory tree, one folder of code and data side by side. There is no friction to combining them, and combining them feels like simplicity.

The entanglement becomes visible only when something forces them apart. Then you discover:

- A hundred scripts that hardcode paths relative to the project root.
- A test suite that assumes the data lives next to the code.
- Configuration files that mix engine settings and state paths in the same structure.
- Imports that rely on relative paths between engine and state.

By the time you notice, the cost to disentangle is enormous, because every assumption is in the wrong place. The right answer is to enforce the separation **before you need it** — when the system is small and the cost of the discipline is trivial.

Specifically, three habits enforce the separation:

1. **Every script resolves its own engine location from its own file path.** Not from a working directory. Not from an environment variable. From `__file__`. This makes the engine robust to being moved, because every script knows where it is regardless of where it gets called from.

2. **Every script reads the state location from one environment variable**, with a sensible default. Not from a constant in code. Not from a config file co-located with the engine. From an environment variable. This makes the state location swappable without code changes.

3. **The engine never imports from the state, and the state never executes from the engine.** They communicate through file I/O, not module imports. If the engine needs a utility that lives near the state, that utility moves into the engine. The engine is self-contained code; the state is self-contained data.

The third habit is the hardest. It feels natural to put a "state utilities" module near the state files, and to import it from the engine. The shared utility is a leak in the abstraction. Force the duplication, or force the utility into the engine where it belongs.

## The actual migration

When the discipline holds, migration is short. Here is the shape:

**Step 1: spin up the new engine in its target location.** The engine is just code. It can be cloned, copied, deployed — whatever moves code in your environment. The state is untouched.

**Step 2: dry-run the new engine against a test state.** Create a scaffolded copy of the state, point the new engine at it via the environment variable, run a single tick of the engine, and verify the outputs. This catches every implicit assumption you missed. Cost: a few minutes. Returns: hours of debugging avoided.

**Step 3: stop the old engine. Start the new engine pointing at the same state.** This is the cutover. With both engines knowing how to find the state via the environment variable, the swap is one process kill and one process start. The state file does not move. The engine's location did, but the state never noticed.

In the migrations I have done, this is a thirty-second cutover. The state is unaffected. The engine's frame counter or job queue continues from where it left off, because the next frame's input is what the previous frame's output produced — and that output lives in the state, which is unchanged.

**Step 4: verify and clean up.** The new engine is running. Watch it for a frame or two. If something is wrong, kill it, re-point the environment variable at the old engine, and start the old one again. The recovery path is symmetric to the migration path because both engines speak the same protocol with the state.

If you have done this right, the system never noticed. Outputs continued. Whatever was depending on the system kept working. The brain moved. The body did not.

## What this pattern unlocks beyond migration

Once the engine and state are decoupled, several things become straightforward that were previously painful.

**Time travel.** A snapshot of the state is a complete world. Running the engine against an old snapshot replays history. There is no special "replay mode" — running the engine against snapshot N produces the same output the engine produced when state N was current. Debugging means picking a snapshot and watching the engine traverse it.

**Parallel runs.** Running two copies of the engine against two copies of the state, with two different versions of the engine code, gives you a controlled A/B comparison. The same input. Different runtime behavior. The output diff is the change. There is no shared dependency, no infrastructure to spin up — just two environment variables pointing at two state directories.

**State as a unit of distribution.** The state can be checked into version control independently. It can be backed up independently. It can be distributed to other machines independently. Each machine has its own engine; the state flows. This pattern shows up in every system where many workers operate on shared data — when the state is the unit, the workers become disposable.

**Engine as a unit of distribution.** Conversely, the engine can be packaged independently. Containerize it. Vendor it. Ship it as a CLI tool. Whatever you want — the engine has no implicit dependency on a particular state location. Anyone can run it against their state.

**Hot swaps and canary deploys.** Roll out a new engine version to a canary state directory. Watch it. Promote it by changing the environment variable. Roll back by changing it again. The state is the constant; the engine is the variable.

These are not new ideas. They are how mature production systems work. What is new for most projects is realizing that the pattern is available **before** you have a mature production system, if you enforce the separation early. The cost when you are small is trivial. The benefit when you are large is enormous.

## The retrofit playbook

If you are reading this and recognizing your own system as entangled, the retrofit is mechanical. Three passes:

**Pass 1: introduce `ENGINE_ROOT` everywhere.** Find every script that uses `os.path.join(some_root, ...)` or relative paths. Replace those with paths anchored to `ENGINE_ROOT`, computed from the script's own `__file__`. Run your tests. Fix the breakage. This pass is largely mechanical.

**Pass 2: introduce `STATE_PATH` from an environment variable.** Find every reference to a state location. Replace it with a function or constant that resolves the state path from `os.environ`, falling back to a default. Update the launcher to set the environment variable explicitly. This pass takes longer because it forces you to find every implicit assumption about state location.

**Pass 3: break the cross-imports.** Find imports from engine modules into state-shaped utilities, and vice versa. Move utilities to the side they belong on. Duplicate where needed. This pass is the hardest, because it surfaces architectural decisions that were never made consciously. It is also where the long-term value lives.

After all three passes, run the dry-run migration test. Spin up a clean copy of the state in a new location. Point the engine at it. Run a tick. If the tick succeeds, the decoupling holds.

The total work is usually a few days for a medium-sized project. The savings start the first time you need to move something.

## What I would tell a team building from scratch

Two pieces of advice.

**Treat the runtime/state separation as a non-negotiable design constraint.** Not "we will keep them somewhat decoupled." Hard separation. The engine never imports from the state. The state never executes from the engine. They communicate through file I/O, with explicit serialization at the boundary. This sounds extreme; in practice it is the only thing that survives.

**Test the migration path before you need it.** Once a quarter, do a dry-run migration. Spin up the engine in a new location. Spin up a copy of the state in another new location. Run the engine against the new state. If it works, you have proven the separation. If it does not, you have caught an entanglement before it became expensive. Make the dry-run part of the routine, like backups.

The hardest migrations are the ones nobody expected to need. The systems that survive them are the ones that were built, from the beginning, as if migration would happen this afternoon. The pattern is small. The discipline is real. The dividend is everything.
