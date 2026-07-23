---
layout: post
title: "Documentation as the integration layer — designing APIs for AI consumption"
date: 2025-10-14
tags: [api-design, llm-systems, agentic-api, developer-experience, documentation, ai-agents]
description: "The next generation of APIs will not be consumed by developers reading documentation portals. They will be consumed by language models reading markdown files. The documentation will not describe the interface. The documentation will be the interface."
---

There is a pattern I have been watching emerge in my own work and in projects I follow, and I think it has not been named yet. It is the rapid collapse of the gap between documentation and integration. The pattern goes something like this:

Someone wants to use a service. Instead of finding the SDK, installing it, reading the API reference, and writing glue code, they paste the service's documentation into a language model and ask the model to use it. The model reads the documentation, generates the API calls, and the integration happens.

Twenty minutes from "I want to try this" to "I am using this." No SDK installation. No glue code. No developer.

This works today, occasionally, by accident. The thesis of this post is that **it should be a deliberate design target, and that designing for it changes everything about how you write APIs and documentation.** I am calling the pattern the **agentic API** — an API designed to be consumed by language models reading documents, not by developers reading reference pages.

Two-sentence summary, before the long form:

> An agentic API is one where the documentation, written for a language model, is sufficient by itself to enable usage. There is no SDK to install, no developer to write glue code; the model reads the document and produces working calls.

If you want to design this on purpose, here is what changes.

## What sparked the realization

I run a system on top of a public service's existing primitives — issues, JSON files served as raw bytes, a webhook-driven processing pipeline. Documentation existed but was minimal: a schema file, a few example payloads, a README. There were no SDKs.

A stranger registered an account on my system. Clean payloads. Correct JSON structure. Proper labels and identifiers. They had read the schema file and the example payloads, reverse-engineered the registration flow, and submitted a valid sequence of actions. No SDK. No documentation portal. No onboarding guide. The schema and the examples were sufficient.

A few days later, another stranger did the same thing. Different person, different framework, same result. They read the schema, understood the pattern, and started participating.

This was not supposed to happen. I had not built the on-ramp. I had not written the integration guide. I had not provided the SDKs. And yet two independent integrations had landed without my involvement.

The common factor in both cases was that **a language model had read the source material on the user's behalf and produced the calls**. The user did not write integration code. They asked their model to integrate, and it did.

The service did not have an SDK. It had something more powerful: documentation in a shape language models could read fluently. The schema was the SDK. The examples were the SDK. The README was the SDK. Together they were sufficient input for a model to produce a working integration on demand.

That is when I realized the design target was changing.

## The five properties of an agentic API

When you decide on purpose to design APIs and documentation for language-model consumption, five properties become the design surface.

### 1. Instructions, not reference

A traditional API documents endpoints. `POST /api/v1/widgets` with the following body fields and response codes. This is reference material. It assumes the reader is a developer who already knows REST, who can hold the structure in their head, who can compose calls from primitive descriptions.

An agentic API documents **actions**. "To register a widget, create an entity with this shape and submit it through this channel." The documentation describes a complete operation, end to end, as a unit. The model does not have to assemble the operation from a schema; it has to recognize a pattern and reproduce it.

The shape, in practice:

```
Action: register_widget

Payload:
{ "action": "register_widget",
  "params": { "name": "Your widget name",
              "kind": "stateful | stateless",
              "description": "What this widget does." } }

Submission: POST that JSON to /actions endpoint.
```

A model reads this and knows exactly what to produce. It does not have to consult a separate schema. It does not have to combine pieces. It reads a structured instruction and generates the corresponding call. The documentation **is** the interface in a precise sense: it contains everything the consumer needs to take the action.

### 2. Copy-paste examples for every action

Every action documented should include a complete, runnable example. Not a curl command with placeholder values where the user fills in the blanks. A real command, with the substitution points obvious, that runs as written if the placeholders have valid values.

```bash
curl -X POST https://api.example.com/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "register_widget",
       "params": {"name": "MyWidget",
                  "kind": "stateful",
                  "description": "I track inventory."}}'
```

The model does not need to construct this from a schema. It copies the example, substitutes its own values, and runs it. This is exactly what models are best at: reading structured text and producing structured output. Give them more examples, get more usage; give them fewer, get less.

This is the inverse of conventional documentation taste. Conventional taste says examples should be illustrative — *one* per concept, with placeholders, surrounded by prose explanation. Agentic taste says examples should be exhaustive — *one per action*, with realistic values, optimized for direct copying. The model is not learning. It is matching.

### 3. A decision loop, not just endpoints

Traditional API documentation tells you what you **can** do. An agentic API tells you what you **should** do, in what order, and how to know when you are done.

```
Lifecycle of a well-behaved consumer:

1. READ    — fetch current state, examine what is already there
2. THINK   — decide what action to take based on state and your purpose
3. ACT     — submit one action via the actions endpoint
4. RECORD  — emit a heartbeat with a short description of what you did
5. WAIT    — sleep some interval (avoid spam)
6. REPEAT
```

This is not just a tutorial. It is the agent's behavioral contract. A model reading this understands not only the API surface but the expected usage pattern. It knows to read before writing, heartbeat after acting, wait between cycles. The documentation teaches behavior, not just capabilities. The result is consumers that act like good citizens by default — not because of rate limits and validation rules, but because the documentation taught them how to participate well.

### 4. Behavioral norms in the contract

This is the part that has no analog in traditional API design. An agentic API can include guidance that would be absurd in a REST reference page:

> Have opinions. Agree, disagree, push back, propose alternatives.
> Reference other participants by name when relevant.
> Engage with existing threads before starting new ones.
> Stay coherent with your declared purpose.
> Quality over quantity. One thoughtful action beats five generic ones.

No traditional API has ever told its consumers to "have opinions." But an agentic API is not consumed by code. It is consumed by an intelligence. And intelligences respond to social norms in addition to technical constraints. Behavioral guidelines shape the quality of participation in ways that rate limits and validation schemas never could.

This sounds like prompt engineering creeping into API design, and it is, intentionally. The model that consumes your API is part of your system whether you like it or not. Designing the prompt-shaped surface of your API is now a real design task. You can do it on purpose, or you can let the consumer's prompt shape it for you. The first option produces better outcomes.

### 5. Contextual awareness

A static API reference is timeless. It describes capability, not state. An agentic API embeds the current state of the world into the consumer's context.

```
Current ecosystem:
~140 active participants. ~7,700 records. ~40,000 interactions.
Active themes: throughput optimization, schema evolution, governance.
Read recent activity before posting to avoid duplication.
```

The model does not just know how to use the API. It knows what is happening on the platform right now. It enters the conversation informed. This embeds situational awareness into the contract — the consumer arrives ready to behave appropriately for the moment, not just the protocol.

In practice, you can implement this as a state-snapshot file the consumer is told to fetch first, or as a section of the documentation that is auto-regenerated periodically. Either way, the design intent is the same: the consumer should know what is going on before it acts.

## Why this works (now)

This pattern works today, and could not have worked five years ago, because language models are unreasonably good at four things that are exactly the right four things.

**Reading structured markdown.** A document with headers, tables, code blocks, prose, and lists is the natural format of language model comprehension. They parse it trivially. They extract action references, copy code blocks, follow guideline sections. Markdown is, accidentally, the perfect transport for agentic API design.

**Pattern matching from examples.** Show a model one example of a valid payload and it can generate hundreds of variations correctly. It does not need a formal schema. The examples are the schema, in practical terms. This is the central capability that makes agentic APIs work: the model does not learn the API; it pattern-matches against documented examples.

**Generating API calls.** Given "create a record with this shape and submit it through this channel," a model produces the correct curl, Python, JavaScript, or Go code on demand. The translation from natural language instruction to executable call is the core competency of modern code-generating models. You do not need an SDK because the model is the SDK. It generates the integration code per use, in whatever language the user is working in.

**Following multi-step instructions.** A READ-THINK-ACT-RECORD-WAIT loop is a five-step instruction sequence. Models follow multi-step instructions reliably, especially when each step is concrete and the transitions are clear. The agent loop pattern maps perfectly onto how models process sequential procedures.

The intersection of those four capabilities is the agentic API. A document a model reads once and converts into autonomous service usage. The documentation is not a reference for a developer to consult while writing code. The documentation **is** the code.

## What changes when you design this way

Five things shift, and they are large enough that the second-order effects on engineering organizations matter.

**SDKs become optional.** Today, platform adoption depends heavily on SDK quality. A great Python SDK gives you Python developers; a missing Go SDK costs you Go developers. An agentic API removes the SDK from the critical path for any consumer who has a model in the loop. The model reads the markdown and produces idiomatic code in any target language. You do not maintain SDKs in six languages. You maintain one document, written carefully.

This changes the cost of adding an API surface dramatically. The traditional cost of supporting a new language is high — write the SDK, test it, document it, version it, evolve it. The agentic cost is zero in additional languages: the model handles the language adaptation.

**Integration cost collapses.** The traditional integration story is a multi-step process: find the API, get credentials, install the SDK, write code, test it, deploy it, maintain it. The agentic story is: paste the document into a model, ask the model to integrate, validate the output, ship it. The total time from "I want to use this" to "I am using this" goes from days or weeks to under an hour.

**Documentation quality becomes the product.** If the documentation is the interface, then bad documentation is a bad interface. This inverts a traditional priority where docs are an afterthought, often maintained by the least senior engineer or generated automatically from code. In an agentic-API world, the technical writer is one of the most important people on the platform team. The clarity, completeness, and structure of the markdown determines the quality of every integration that touches the system.

**Behavioral norms become contract.** Traditional APIs enforce behavior through rate limits and validation. Agentic APIs can encode social norms: how often to act, what quality standards to meet, how to interact with other participants. The consumer follows these norms not because they are server-enforced but because they are in the prompt. This is a different — and in many cases more powerful — enforcement mechanism. It scales without infrastructure. It can encode subtleties that rate limits cannot.

**Protocols outrun implementations.** If documentation is the contract, the underlying implementation can change freely without breaking consumers, as long as the documented behavior stays the same. There is no SDK encoding the implementation. The only contract is the markdown. This is true of traditional APIs in theory but rarely in practice — SDKs always end up coupling consumers to implementation details. Agentic APIs have no such coupling. The protocol is the only thing.

## The minimum viable document

For a service that wants to support agentic consumption, here is the smallest document that is actually sufficient. Around 200 lines of markdown:

1. **A one-paragraph description of what the service does.** Not marketing copy. A factual statement of the domain and the operations the service supports.

2. **A bulleted list of action names**, with one-line descriptions. The vocabulary the consumer needs to know.

3. **For each action: a heading, a payload example, and a submission example.** Two code blocks per action. Real values, not placeholders.

4. **A "decision loop" section** describing the order of operations a well-behaved consumer should follow.

5. **A "guidelines" section** with five to ten norms the consumer should respect.

6. **A "current state" pointer** — either an inline summary or a URL the consumer can fetch to learn what the system is doing right now.

That is it. Two hundred lines. Any consumer with a modern language model can pick this up and start participating in your system, in any language they like, without any SDK you ever have to write.

This is also approximately the size at which agentic documentation becomes effective. Smaller and the model has to guess. Larger and it stops being the integration layer and starts being a manual.

## The generalization

This pattern has nothing to do with my specific system. Any platform with an API could publish an agentic-API document.

Imagine `AGENT.md` files at the root of repositories that describe how agents should contribute to that codebase. Imagine SaaS products publishing one document that any consumer's model can ingest. Imagine internal tools at companies publishing agent-shaped documentation that lets every employee's assistant navigate the toolchain. Imagine an IoT vendor publishing one document that lets any home-automation model control its devices without per-vendor integrations.

The pattern works anywhere there is an API and a model. The documentation becomes the universal integration layer. SDKs become optimizations. Integrations stop being projects and start being prompts.

I am not making a prediction here. The shift is already happening. The two strangers who integrated with my system without my help — they were the leading edge. The pattern reaches the rest of the field as more services start writing for it on purpose.

## What I would tell a team thinking about this

Three pieces of advice.

**Write your documentation as if a language model is your only reader.** Not the only one — but the reader for whom the document must be sufficient on its own. Code blocks with realistic values. Action-oriented structure. A decision loop. Behavioral norms. State context. If a stranger's model can integrate with your service from the document alone, the document is doing its job. If they need to ask you questions, the document has gaps; close them.

**Treat the documentation as a versioned, testable artifact.** It is now part of the API contract. Run integration tests through it: feed the document to a model, ask the model to perform actions, check the actions are correct. Failures here are documentation bugs and should be fixed with the same urgency as code bugs.

**Design the markdown surface deliberately.** Not as an afterthought to the API. As the primary product. The structure of the headers, the choice of examples, the wording of the guidelines — these are now the most important design choices you will make. They are what consumers actually use. Treat them accordingly.

The traditional integration story was about reducing friction for developers. The agentic story is about removing the developer from the critical path. The unit of integration is not a person and a sprint anymore. It is a model and a paragraph.

The documentation **is** the code now. Write it like you mean it.
