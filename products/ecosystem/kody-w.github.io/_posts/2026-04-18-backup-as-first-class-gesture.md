---
layout: post
title: "Backup as a First-Class User Gesture"
date: 2026-04-18
tags: [ux, backups, data-ownership, doctrine, exports]
---

Every personal-data tool you build should ship Export and Import buttons on day one. Not in settings. Not behind a CLI. In the main UI, next to the search box, where people will see them.

The reasoning is simple. The promise of "you own your data" is meaningful only if exercising that ownership is a one-click gesture. Buried exports are not exports — they're a legal compliance feature. People who would have backed up their data don't, because the path is too long. People who would have migrated to a fork don't, because the export is incomplete or in a custom format. Friction kills ownership.

A first-class export gesture has four properties:

**Visible.** The button is in the persistent UI chrome, not under a triple-nested menu. It says "Export Backup," not "Download Data" or "Account Settings → Privacy → Request Data Archive."

**Synchronous.** Click, get a file. Not "we'll email you in 24 hours." Not "your archive is being prepared." The browser already has all the data; it can serialize it in milliseconds. Make it instant.

**Lossless.** The exported file contains *everything* needed to reconstruct the working state. Not a marketing-slide summary. The raw fields, the original frontmatter, the unprocessed body, the file paths, the metadata. If something would be lost on round-trip, it's a bug.

**Round-trippable.** Import accepts what Export produces, byte-for-byte. The same file goes out and comes back in. No custom converter. No migration script. No documentation explaining which fields to map where. The format is whatever Export wrote, and Import knows how to read it. This is the property most exports fail.

The Import side has its own requirements:

**Visible.** Same chrome as Export. Same row of buttons.

**Preview before commit.** Importing should refresh the live in-memory view immediately. The user sees what they'd be getting. Then they decide whether to make it permanent.

**Safe to merge.** Imports merge with existing data by stable key (a hash, a UUID, a primary identifier). The same card imported twice doesn't duplicate. Updates are detected and applied. Adds are flagged separately so the user sees what changed.

**Permanent path is documented.** The live view is in-memory only. The import is real after the user takes a separate action — committing files to the repo, persisting to localStorage, syncing to a remote. The UI tells them what that next step is.

For a static-site backed personal tool, the pattern that works:

- Export downloads a JSON file containing the full data
- Import accepts that JSON, merges into the in-memory grid for preview, and *also* downloads a "bundle" file in a format the build script can consume
- A short Python script (stdlib only) reads the bundle and writes the underlying source files into the repo
- The next build picks up the new sources and the import is permanent

This is twenty minutes of work to add to most tools. The benefit is permanent: any user can leave with everything, any user can restore everything, any user can fork the entire collection and host it themselves. The data ownership promise becomes literally true.

The version of this that doesn't ship is the version where exports require a CLI. Or where Import works for some fields but not others. Or where the round-trip drops formatting. Each of those failures is a small one, individually. Collectively they mean nobody actually backs up.

Ship the buttons. Make them lossless. Make them round-trip. Then the promise holds.
