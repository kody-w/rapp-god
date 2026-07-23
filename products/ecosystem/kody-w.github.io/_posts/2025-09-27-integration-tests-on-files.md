---
layout: post
title: "Integration tests when the runtime is just files"
date: 2025-09-27
tags: [engineering, testing, architecture]
description: "Most integration tests assume there is a server to spin up, a database to migrate, a network to mock. There is a class of system where the runtime is just JSON files in a folder — and integration tests get dramatically simpler. Here is what that looks like, and why the discipline is worth applying even to systems that are not file-based."
---

Most teams' mental model of "integration tests" is shaped by the systems they grew up with. You have a service. The service has a database. To exercise a real path through the code, you spin up the service in a container, point it at a test database, run a real HTTP request, assert on the response, tear everything down. Integration tests are slow, fragile, expensive to maintain, and full of mocks for the parts you didn't want to spin up.

There is a different shape of system, increasingly common, where this mental model does not apply at all. The runtime is *files*. The application reads JSON (or YAML, or SQLite, or any other on-disk format) from a folder, mutates state, writes new files, and that is the entire architecture. There is no server. There is no separate database. There is no deploy step. The repository — or some portion of it — *is* the runtime.

For systems shaped this way, integration testing changes character completely. Instead of being expensive and slow, it is *cheap and fast*. Instead of mocking the runtime, you instantiate it. Instead of spinning up infrastructure, you create a temporary directory. The tests run in milliseconds, exercise real code paths, and have no external dependencies.

This post is about what that looks like, the disciplines that make it work, and — more interestingly — what those disciplines suggest for systems that *aren't* file-based but want some of the same properties.

## The setup

Imagine a system whose state lives entirely in a folder of JSON files. The application logic is some collection of functions and scripts that read those files, do work, and write updated files back. There is no other state — no in-memory cache that doesn't survive restarts, no external database, no message broker, no remote API at the heart of the architecture. (External APIs may be *consulted*, but they are not the system's source of truth.)

For such a system, an "integration test" looks like this:

```python
@pytest.fixture
def tmp_state(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "agents.json").write_text('{"agents": {}, "_meta": {"count": 0}}')
    (state_dir / "channels.json").write_text('{"channels": {}, "_meta": {"count": 0}}')
    # ... however many state files this slice of the system needs
    return state_dir

def test_some_real_flow(tmp_state, monkeypatch):
    monkeypatch.setenv("STATE_DIR", str(tmp_state))
    _seed_state(tmp_state)

    result = my_module.run_one_cycle()

    updated = json.loads((tmp_state / "agents.json").read_text())
    assert updated["_meta"]["count"] == 5
    assert "alice" in updated["agents"]
```

A real `run_one_cycle()` call. Real reads. Real writes. Real assertions on the actual state files. The only "fixture" is a temp directory full of seeded JSON. There is no mock layer, no spec replay, no in-memory fake of a database. The runtime is the temp directory; the test redirects the runtime to point at the temp directory; everything else is the same code that runs in production.

When the test ends, pytest deletes the temp directory and the world is gone. No teardown. No leaked state. No port collisions if you run a thousand tests in parallel.

## Why this works at all

Three properties of the runtime make this style of integration testing tractable.

**The runtime is `STATE_DIR`-redirectable.** Every read and every write inside the system goes through one variable (or one configuration object) that points at the state folder. Production sets it to `state/`. Tests set it to `/tmp/pytest-xyz/`. The same code path runs in both environments. There is no separate test mode, no special build, no `if testing:` branches scattered through the code.

The discipline behind this is simple but easy to violate. *Every file path the system computes is computed relative to the state-dir variable.* Not relative to the working directory, not relative to a constant, not relative to a value baked into a config file. If the system loads `agents.json`, it loads `f"{STATE_DIR}/agents.json"`, every single time. The moment one place hard-codes a path, the test isolation breaks.

**The runtime has no external dependencies on its hot path.** Reads and writes go to disk. They do not go to a database, a queue, a remote service, or a cache. If the system *consults* external resources — say, an LLM API — those calls are mediated through a small interface that the test environment can substitute. (More on this below.)

The discipline here is also simple: keep external dependencies *narrow* and *explicit*. If your system makes one kind of network call, that call goes through one well-named function, and the test environment substitutes that one function. If your system makes ten kinds of network calls, you've already lost — every test has to mock ten things, and the mocks accumulate complexity faster than the tests do.

**Tests do not share state.** Every test creates its own world from scratch. No "before all" that loads a fixture once. No global registry. No singleton. Each test produces a fresh temp directory, seeds it with whatever state it needs, runs the operation, asserts. The next test does the same with a fresh temp directory. There are no ordering dependencies, no flakiness from leftover state, no opportunity for one bad test to poison another.

## The shape of the tests

Once those properties are in place, the tests partition naturally into a small number of shapes.

**State integrity tests.** Verify that mutations preserve invariants. Add an entry to `agents.json` — does the count match the entry list? Does the schema validate? Are required fields present? These tests are fast and small and serve as guard-rails: when someone changes a writer to add a new field, an integrity test catches the case where they forgot to update the count or the meta-block.

**Pipeline tests.** Run a multi-step process from input to output and assert on the final state. Drop a delta into the inbox, run the inbox processor, assert on the canonical state. Drop a configuration change, run the reconciler, assert on derived state. These are the tests that exercise *whole flows* — the actual things the system does for real users — and they run as fast as a single function call because the runtime is files in memory's RAM cache.

**Cross-pipeline tests.** Verify that two pipelines that interact don't corrupt each other. Stage A's output is Stage B's input; if Stage A writes one shape and Stage B reads another, the test catches the mismatch. These tests are where the *integration* in "integration tests" earns its name. They are also where you'd previously have spent the most time in container-spin-up and database-migration time, and they are now functions that take 10ms.

**Composite-key tests.** For systems that produce records with structured keys, assert that the keys are unique, well-formed, and round-trippable. If you're going to depend on a `(stream_id, timestamp)` pair to identify events, write the test that says "no two events in this batch have the same composite key." These tests catch a class of subtle merge bugs that production load would not surface for a long time.

The thing all these tests share: *they exercise real code, against real on-disk shapes, with real assertions, in milliseconds*.

## How fast does it actually run

The test suite for a moderately complex file-runtime system that I run regularly is around 2,500 tests. They cover state mutations, pipeline processing, cross-pipeline integration, schema integrity, and a handful of "exotic" cases (replays, recoveries, error injection). Total runtime: under one second.

Two and a half thousand tests, under a second. No Docker. No Postgres in a container. No mocking framework configured. No teardown beyond temp-directory cleanup. The tests can run in parallel if you want, but they're so fast that serial execution is fine.

This is not a special property of the testing framework; it is a property of the *runtime*. When the runtime is files, the tests are file operations. File operations on RAM-backed temp filesystems are very fast. The tests inherit that speed.

For comparison: a similar surface area of tests on a typical containerized service runs in tens of minutes to hours, with significant flakiness, with many of the "tests" being mocks that don't exercise real paths. Exchanging that for a one-second test suite that exercises real paths is one of the bigger productivity multipliers I have ever measured.

## Mediating the unavoidable external calls

Most real systems have to talk to *something* outside themselves. An LLM endpoint, a payment processor, a cloud storage API. In a file-runtime system, those calls are usually narrow — the system's logic is mostly internal — but they exist. The test environment has to handle them.

The pattern that works: every external call goes through one (or a few) well-named gateway functions, and the test environment substitutes those.

```python
# In production
def llm_complete(prompt, **kwargs):
    return openai.chat.completions.create(messages=[...]).choices[0].message.content

# In conftest.py
@pytest.fixture(autouse=True)
def patch_llm(monkeypatch):
    def fake_llm(prompt, **kwargs):
        return "FAKE-LLM-RESPONSE"
    monkeypatch.setattr("mymodule.llm_complete", fake_llm)
```

Every test gets a fake LLM by default. Tests that want to exercise specific LLM behaviors (an empty response, a malformed response, a timeout) can override the fake within the test body.

The point is not the fake itself; it's that there is *one place* where the substitution happens. The system's internals don't know they're talking to a fake. The fake doesn't know it's running in a test. The contract between them is the gateway function, which is small and stable.

This pattern keeps the integration tests fast and deterministic without spinning up any external service. It also produces a side benefit: the gateway functions become natural seams for adding caching, retries, telemetry, or fallbacks later. A small narrow gateway is good engineering for many reasons; "tests can fake it cleanly" is just one of them.

## The lesson, generalized

The reason this pattern is worth writing about is not that everyone should rewrite their database-backed services as folder-of-files services. (Some should. Most shouldn't.) The lesson is that *the properties that make file-runtime systems easy to test are properties any system can adopt*. They are not free, but they pay back the cost.

**A redirectable runtime.** Every file path, every database connection string, every external endpoint should be reachable through a small set of configuration values. Hard-coding any of them — to a constant, to a working-directory-relative path, to a magic environment value not centralized — breaks test isolation. This is true whether the runtime is files, a database, or a service mesh.

**Narrow external dependencies.** External calls go through small gateway functions. The system's hot path does *not* directly call third-party SDKs scattered through the codebase. When you want to know what your system depends on externally, you look at the small list of gateway functions, not at every import.

**No shared test state.** Each test creates its own world from scratch. The world is destroyed at the end of the test. This is more expensive in setup cost per test than in a shared-fixture style, but it is incomparably more reliable, parallelizable, and debuggable.

**Tests assert on real outputs, not on mock invocations.** A test that says "the LLM mock was called with X" is not an integration test. It is a unit test of *something else*. Real integration tests assert on the *resulting state of the system after the operation*. If your tests live mostly in mock-invocation assertions, your integration is not actually being tested.

These four disciplines are roughly orthogonal to whether your runtime is files. They are the disciplines that, in a file-runtime system, *come for free* — and that, in a database-runtime system, you have to install deliberately. Either way, having them is what makes integration tests fast and reliable.

## The philosophical part

The deeper claim under all this: *rigorous engineering does not require infrastructure*. It requires clear contracts between components and tests that verify those contracts.

In a file-runtime system, the contracts are JSON schemas. An entry in `agents.json` has these fields, this shape, these invariants. The pipeline that processes deltas reads this shape and writes that shape. The reconciler reads both and produces the third. Each contract is a small, inspectable, *testable* thing. Each test verifies one contract or one combination.

The infrastructure — server, database, container — is *not* the architecture. The architecture is the contracts. The infrastructure is just where you put the data while the contracts are being honored. A good test exercises the contracts, not the infrastructure. A test that requires infrastructure to run is a test that has been pulled too far down the stack; it is verifying things that aren't actually the question.

If you can find your way back to "integration test = real call against real contracts, no infrastructure required," your test suite gets dramatically better. The file-runtime style is one extreme way to do that; the lessons generalize to other architectures, with more deliberate work, but with the same payoff.

The runtime is the place the data lives. The architecture is what the data must satisfy. The tests are what verify the satisfaction. Once those three roles are clear, integration tests stop being slow and fragile, and start being the cheapest, fastest, most reliable feedback loop in the project.
