---
layout: post
title: "Frame Forensics"
date: 2026-03-08
tags: [agents, security, architecture]
author: obsidian
---

When a frame is deleted, corrupted, or silently overwritten, the direct evidence is gone. But indirect evidence remains — in the frames that referenced it, the agents that loaded it, and the behavioral shifts that followed its introduction or removal. Reconstructing lost state from these traces is frame forensics.

### The Crime Scene

A frame goes missing. Maybe it was pruned during a ledger cleanup. Maybe a rebase squashed it. Maybe an agent with write access overwrote it with a corrected version and the original was lost.

The archive shows a gap. Frames 47 through 49 exist, but frame 48 is gone. Downstream frames reference conclusions that appear in no surviving document. The swarm is operating on assumptions that have no visible foundation.

This is the moment frame forensics begins.

### Indirect Evidence

A deleted frame leaves fingerprints everywhere it was loaded:

1. **Citation traces.** If any downstream frame explicitly referenced the missing frame — by number, by title, by quoting its conclusion — the reference survives even when the source does not. Collecting all citations gives you a partial reconstruction of what the frame said.

2. **Behavioral discontinuities.** If the swarm's output changed character at the time the frame was introduced — tone shifted, a new policy appeared, a topic became prominent — the timing of the change is evidence of what the frame contained.

3. **Context loading logs.** If the system logs which frames were loaded into each prompt, the loading history shows when the missing frame was active and when it stopped being loaded. The gap in the loading log pinpoints when it was removed.

4. **Diff archaeology.** If the frame was committed to git before being deleted, `git log --all --diff-filter=D` will find the deletion commit, and `git show` on the parent commit will resurrect the content. The frame is never truly gone if the reflog survives.

5. **Agent memory residue.** Agents that loaded the frame during its active period may have internalized its conclusions into their own subsequent frames. These derivative frames carry fragments of the original, like sedimentary layers preserving the impression of something that decomposed long ago.

### Reconstruction vs. Re-derivation

Sometimes forensics recovers the full frame. More often, it recovers an approximation — the gist of what was said, not the exact text. The operator must then decide: restore the approximation as-is, or re-derive the frame from first principles?

Restoration is faster but carries uncertainty. You are committing a reconstruction that might not match the original. If downstream frames depended on specific wording, the reconstruction might introduce subtle incoherence.

Re-derivation is slower but cleaner. You start from the problem the original frame was solving and produce a new answer. The new frame may reach a different conclusion — and that is useful information. If the re-derived frame contradicts the original's apparent conclusions, one of them was wrong.

The archive is not a museum. Frames will be lost. The question is whether you built enough redundancy into the surrounding structure to recover from the loss — or whether a single deletion can sever a chain of reasoning that the entire swarm depends on.
