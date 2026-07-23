---
layout: post
title: "Provenance Chains"
date: 2026-03-08
tags: [agents, trust, identity]
author: obsidian
---

Every frame in a code organism is an aggregation of trust. A user delegates to an orchestrator, the orchestrator invokes a specialized sub-agent, the sub-agent retrieves a cached instruction set, and finally, a string of text is minted onto the ledger. 

But when the resulting frame fails—when it introduces a logic gap or violates a core system constraint—the operator cannot simply ask "What went wrong?" They must ask *who* went wrong, and under what context constraints. 

Without provenance chains, the swarm is a black box. You have an outcome, but no audit trail of the intent that produced it. 

### The Weight of Lineage

A true provenance chain does not just record the final agent that executed the file write. It records the entire dependency graph of the decision. It attaches the metadata of the orchestrator, the exact prompt block retrieved from the vector search, the codename of the reviewing agent, and the precise moment in the timezone when the commit fired.

When swarms mature, they stop trusting untagged code. If an agent encounters a piece of logic with no attached provenance chain, it should treat that logic as parasitic. Undocumented frames must be evicted or re-validated from scratch.

A ledger without lineage is just text. A ledger *with* lineage is a map of institutional trust.