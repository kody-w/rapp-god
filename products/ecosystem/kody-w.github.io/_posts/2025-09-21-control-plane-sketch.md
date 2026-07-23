---
layout: post
title: "When does a script become a control plane?"
date: 2025-09-21
tags: [architecture, infrastructure, scaling]
description: "There is a common shape in scaling stories — a hand-run shell script gets called more and more, until one day a human running it from a laptop is the wrong shape. Here is how to recognize that moment and how to design the smallest possible thing that replaces the human, without overshooting into a Kubernetes operator."
---

Almost every team that scales a service-per-customer or environment-per-tenant workload eventually runs into the same wall, and they all run into it the same way.

In the beginning, you have a shell script. The script provisions one instance of whatever the unit of scale is — a customer environment, a worker, a tenant database, an isolated runtime. You wrote it carefully. It is idempotent. It prints the URL of the new thing when it finishes. You run it from your laptop. You run it once per request, manually, watching the output. It works. The first ten or thirty or fifty calls are unremarkable.

Then one day someone asks for a hundred. You imagine running the script a hundred times, watching a hundred outputs scroll past, copying a hundred URLs into a hundred onboard pages. The math doesn't work. You can't do it by hand, and yet the script is still the right *unit* of work — it knows how to make one of these things appear, and it is the only thing on the team that does.

That is the moment a control plane has to exist. Not before. Not later. The trick is to build the smallest possible thing that replaces the human running the script, without accidentally building a distributed-systems platform you don't need yet.

This post is about that smallest possible thing — what it has to do, what it explicitly should not do, and the data shape that keeps it boring.

## What the gap actually is

The provisioning script does the load-bearing part. It calls into whatever your cloud's primitives are, makes the resources appear, configures them, and returns the URL. None of that is the problem. The problem is everything *around* the script:

- A *human* decides when to run it.
- A *human* watches the output to know when it's done.
- A *human* reads the URL out of the terminal.
- A *human* pastes the URL into the next thing — the onboarding page, the customer email, the registry of "things that exist."
- A *human* notices when it fails and decides whether to retry.

Each of those was fine for one or ten. None of them is fine for a hundred or a thousand. A control plane is the small piece of software that takes those five human roles and replaces them with API endpoints and a worker pool, and *nothing else*.

The single biggest mistake when building one of these is to also start replacing things the script already does well. If the script provisions reliably, do not rewrite the provisioning logic. If the script is idempotent, do not bake idempotency into the orchestrator. The control plane orchestrates a thing that already works; it does not rebuild the thing from scratch.

## The wire surface, kept small

A useful control plane needs roughly five endpoints. More than that and you are building a platform; fewer and you can't actually replace the human.

```
POST   /provisions                  → create one (returns job_id, async)
GET    /provisions/jobs/{job_id}    → poll provisioning status
GET    /provisions/{resource_id}    → look up a finished resource
DELETE /provisions/{resource_id}    → tear it down
GET    /health                      → fleet stats
```

The split between `job_id` and `resource_id` is the most important detail in this sketch.

Provisioning is asynchronous and slow — usually minutes. The create call cannot block; it has to return immediately so the caller can move on. So the create call returns a `job_id`, which is a handle to the in-flight work. The caller polls until the job resolves to a `resource_id`, which is the durable name of the actual created thing.

`resource_id` is what survives in the database, what other systems reference, what a future delete call uses. `job_id` is ephemeral — useful for the duration of the create operation, then disposable. Conflating them is a classic mistake that leads to either a control plane that blocks on creation (bad for throughput) or one that loses track of what it created (bad for everything).

The `/health` endpoint is the operator's dashboard in JSON form. Total provisioned, currently active, currently in-flight, errored. Enough to know whether things are healthy without standing up a separate metrics stack.

## The data shape, kept smaller

One row per resource. Eight columns is plenty for the first version.

```
resource_id     text primary key
owner           text                -- who asked for it
region          text                -- where it lives
runtime_target  text                -- what flavor of cloud primitive
deploy_ref      text                -- code/version pinned to this resource
status          text                -- provisioning|active|errored|deleted
url             text                -- how to reach it
created_at      timestamptz
last_seen       timestamptz         -- last successful health check
```

That is the schema. *Where* it lives is a function of how many rows you actually expect.

For the first thousand resources: a JSON file on disk, written atomically, is fine. It sounds embarrassing but it is operationally trivial — back up the file, you've backed up the system. Restore the file, you've restored the system.

For the first hundred thousand: SQLite, with the file replicated to object storage with [Litestream](https://litestream.io/) or equivalent. Still embarrassingly simple. Still survives a single-machine failure.

For the first ten million: PostgreSQL, with the schema above and a real backup story. Still nine columns.

The principle: pick the storage that matches the cardinality you actually have, not the cardinality you imagine. Each tier of storage carries operational cost. Do not pay it before you need to. The schema is the same at all three tiers, so migrating later is straightforward — export rows, import rows.

## The worker pool, kept boring

The worker pool is where it is most tempting to overbuild. Resist.

What it has to do: pop a job off a queue, run the existing provisioning script as a subprocess, capture its output, parse the URL out of it, update the row from `provisioning` to `active` (or `errored` if the script returned non-zero), and pick up the next job. Each worker is a process that loops on a queue.

For the first version, this is two or three workers on a single machine, each running `subprocess.run("./provision.sh ...", capture_output=True)` and parsing the URL out of stdout. The queue is a table in the same database the resource state lives in. There is no message broker. There is no distributed coordinator. There is a `SELECT ... FOR UPDATE SKIP LOCKED` pattern in PostgreSQL, or its equivalent on whatever store you picked.

Provisioning takes minutes. The work is safe to retry — your script was already idempotent, that was the entry condition. So the failure model is simple: if a worker dies mid-job, the next worker picks the job back up, the script re-runs, and the result is identical because the script is idempotent. You don't need an exotic execution layer. You need a small queue and a reasonable timeout.

This is where the control plane gets to feel boring. The interesting part is the API contract above. The execution underneath is `subprocess.run` against a shell script you already debugged. Don't make it more than that.

## What the control plane does not do

The list of things the control plane *should not do* is longer than the list of things it should, and it is worth being explicit about.

**It does not host the resources.** Each provisioned resource runs wherever the script puts it — a managed service, a container platform, a cloud function, a VM. The control plane never serves user traffic. It only orchestrates lifecycle.

**It does not route traffic.** Each resource has its own URL. DNS handles routing. The control plane is not a load balancer or a proxy.

**It does not run a per-resource scheduler.** The cloud primitive your script provisions has its own scheduler — that's why you picked it. Lambda scales requests. Cloud Run scales requests. Managed databases scale connections. The control plane does *not* try to control how the resources scale internally; that is what the cloud's runtime is already for.

This is the most important constraint, and it is what keeps the control plane from turning into Kubernetes. A Kubernetes operator is the right shape when the unit of scale is a container that needs request-level scheduling. The unit of scale here is one *cloud-native primitive* per tenant, and the primitive does its own scheduling. A general-purpose orchestrator on top of self-scheduling primitives is a category error — you'd be running a control loop reconciling desired state against actual state at the request level, and the cloud is already doing that for you.

**It does not handle billing.** Per-tenant cost attribution is a real product question. It is not the *control plane's* question. The control plane records what it created and when. Billing is a downstream consumer of that data.

**It does not handle auth, in the first cut.** The first version is single-tenant: the control plane runs on infrastructure the operator owns, and the only caller is the operator's tooling. Authentication shows up the day a second operator does. Until then, network isolation is enough.

These are not "we'll add it later" placeholders. They are deliberate boundaries that keep the control plane from absorbing problems that don't belong to it.

## What the MVP costs to build

A single-binary service in any reasonable language exposing the five endpoints above. SQLite (or a JSON file) for state. One worker process that shells out to the existing provisioning script. The whole thing is five hundred to eight hundred lines.

The provisioning script is the load-bearing part. It already exists and you already trust it. The control plane is a thin shell around something you have already debugged in production-shaped conditions. That is the right cost ratio: a small amount of new orchestration code wrapping a large amount of proven execution code.

Compare that to the temptation. The temptation, when you reach the "we need to provision a hundred of these" moment, is to also rewrite the provisioning. To also build observability. To also build billing. To also build auth. To also build a UI. Each of these is a quarter of work, and each of them produces zero new provisioned resources until *all* of them are done.

The boring control plane gets you provisioning a hundred resources by tomorrow. The platform gets you provisioning a hundred resources after a quarter, with a thousand other features you didn't have on the day you needed the hundred.

## When to revisit

Eventually the boring control plane has to grow up. Some signs:

- *A second operator wants to use it.* Add auth. Don't add it before this.
- *Provisioning is slow enough that one worker can't keep up.* Add more workers. If they're on the same machine, that's a config change. If they need to be on different machines, that's when the queue stops being a database table and starts being a message broker.
- *The fleet is bigger than your storage choice can hold cheaply.* Migrate the schema (same shape) to the next tier — JSON file → SQLite → PostgreSQL. The export-and-import is straightforward because the schema didn't change.
- *Multiple cloud targets.* The `runtime_target` column was nullable for a reason. When the second target shows up, fill it in. The provisioning script gets a `case "$runtime_target"`. Nothing else changes.

Each of these is a *response to evidence*, not a thing you build prophylactically. You build the small thing first. You let it run. The places it strains tell you what to do next, and the strain is much more informative than your imagination of what the strain might be.

## The pattern, in one sentence

A control plane is the smallest piece of software that turns a working provisioning script into a callable API. It owns lifecycle (create, list, delete, status), nothing more. The first version is a few hundred lines wrapping a script you already trust. Everything you'd be tempted to add — request routing, auth, billing, scheduling, container orchestration — is a separate problem with a separate cost, and adding it before you need it is what turns a useful tool into a project.

Build the boring shell around the trusted script. Ship the hundred resources. Add complexity only when the strain proves you need it.
