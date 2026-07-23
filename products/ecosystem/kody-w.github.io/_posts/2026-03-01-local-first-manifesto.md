---
layout: post
title: "The Local-First Manifesto: No Server, No Permission, No Excuses"
date: 2026-03-01
tags: [zero-cost, architecture]
---

**I. Your application should work without the internet.** Not "gracefully degrade." Work. Fully. The network is a convenience, not a dependency.

**II. Your data should live on the device that created it.** Cloud sync is a feature, not a requirement. The user's device is the source of truth. The server is a backup.

**III. Your AI should run where your data lives.** If your data is on the device and your AI is in the cloud, you've created an unnecessary round-trip, an unnecessary dependency, and an unnecessary privacy risk. Ship the model. Run it locally.

**IV. Your infrastructure cost should approach zero as your user count approaches zero.** A product with zero users should cost zero dollars to run. Static files. Client-side compute. Serverless functions for the rare write operation.

**V. Your application should be forkable.** If a user can clone your repo and have a working instance, you've achieved maximum portability.

**VI. Your state should be human-readable.** JSON over binary. Text over blobs. If you can `cat` the state file and understand what it says, you can debug any problem without special tools.

**VII. Your history should be immutable.** Every state change should be committed. The commit log is the audit trail. This is not optional for systems where correctness matters.

**VIII. Your system should be testable by running it.** Not "testable with a mock." Run the actual system with actual inputs and observe actual outputs.

**IX. Your dependencies should be few and your constraints explicit.** Every dependency is a liability. Every implicit assumption is a bug waiting to happen.

**X. Your failure should be permanent and visible.** Don't hide failures behind retries and recovery. Make them visible, permanent, part of the historical record. A system that hides its failures can't learn from them.

These aren't rules. They're values. When you don't know which way to go, lean local. The network will fail. The server will go down. The API will change its pricing. The only thing you can depend on is what's already on the device. Build for that.
