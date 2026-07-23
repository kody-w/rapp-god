---
layout: post
title: "Choose your data store by access pattern"
date: 2025-10-03
tags: [architecture, data-storage, design-decisions, content-management]
description: "I run two writing surfaces. One stores its content in a database. The other stores its content in markdown files. They have opposite storage models because they have opposite access patterns. Most teams make this choice once for the whole company and pay for it forever."
---

I run two writing surfaces. One is a community where many authors post in real time, threaded comments stack up, reactions are constantly being added, and the whole thing is meant to be read live. The other is a personal blog where one author writes long-form arguments and the work is meant to last.

Same author. Same toolchain. Both deploy through the same continuous-integration pipeline. Same publishing cadence in raw count of words per week. Same server, even.

Completely opposite storage models.

The community lives in a database. Posts are rows. Comments are rows. Reactions are rows. There are tens of thousands of records. They have a backend, a web UI, an API, and full-text search.

The blog lives in markdown files. Each post is a file. There are hundreds of files. There is no backend, no API, no reactions, no comments. Just a static site generator and a flat directory.

The split is load-bearing. Not aesthetic. Not "I happen to like markdown." The two surfaces *have to* store their content differently because they have fundamentally different access patterns. Choosing the wrong one for either would make that surface unusable within weeks.

Most teams choose a default storage model once — usually whatever the framework defaults to, or whatever the founder is comfortable with — and apply it to everything. That is fine when the access patterns of all their content surfaces happen to match the default. It is a slow disaster when one of them does not. This post is about how to recognize which is which.

## What "access pattern" means

Access pattern is the shape of how content is read and written, considered along five axes:

1. **Concurrency.** How many writers, how often. One person occasionally? Many people simultaneously? Robots writing in bulk?
2. **Mutability in context.** Are records edited after creation? Often? By whom? In what kind of operation — single fields, full-record overwrite, threaded additions?
3. **Read pattern.** Are records typically read alone, in lists, in queries, in feeds? Sorted, filtered, paginated, search-indexed?
4. **Durability requirement.** How long does the content matter? A day? A year? Forever?
5. **Portability requirement.** If you had to leave the platform tomorrow, how easily could you take the content with you?

Different content surfaces score very differently across these. The mistake is treating storage as a one-size choice for the whole organization, instead of a per-surface choice driven by access pattern.

## The community: a database problem

A community for many authors is a database problem. Look at the access pattern.

**Concurrency.** Many authors writing simultaneously, often hundreds. Robots and automation pushing content at machine pace. Comments arriving as fast as people can type.

**Mutability in context.** Posts are barely edited but constantly *added to* (comments). Reactions append continuously. Moderation flips lock and pinning states. Every action mutates *something* about an existing record.

**Read pattern.** Almost always in lists: feeds, threads, search results, activity timelines. Almost never read in isolation.

**Durability requirement.** Most posts are short-shelf-life. Today's discussion fades into next week's archive. The platform mostly cares about the recent window.

**Portability requirement.** Low. The content is bound to the social context — the threads, the people, the reactions. Lifting it out of that context is mostly meaningless.

Now imagine storing all of that in markdown files in a git repository.

Every post is a file. Every comment is a file? Or is it a section in the post's file? Every reaction mutates a file. The commit graph is unreadable — one author's commit per minute, hundreds of authors, machine-rate appends. Two people commenting on the same thread within the same second produce a merge conflict the system has to resolve in real time. Search requires re-indexing every commit. Feeds require walking the file tree. The "list" operation that the read pattern needs constantly is the slowest operation the storage layer offers.

This is not a small mismatch. It is a fundamental one. Markdown-in-git for a real community would be unusable within hours of going live.

The right choice for a community is a system designed for high-write concurrency, mutable records, list-shaped reads, secondary indexes, and full-text search. That is a database. Use whatever flavor — relational, document, graph — fits the queries. The point is that you need actual storage with an actual query layer.

## The blog: a flat-file problem

A personal blog is the opposite case in every dimension.

**Concurrency.** One author. Maybe a few minutes per day. There is never a write conflict because there is never a second writer.

**Mutability in context.** Posts are written once and lightly edited. Edits happen in the author's own pass; nobody else touches them. There are no comments, no reactions, no threading. The content is essentially append-only in the directory and edit-in-place per file.

**Read pattern.** Whole-post reads. Some list views (the index page, the tag pages), but the dominant pattern is "this URL → render this single post." Search is welcome but not load-bearing — readers usually arrive from a link, not a query.

**Durability requirement.** I want to read these in ten years. The content is supposed to outlast any specific platform decision. Some essays I want my grandkids to be able to find.

**Portability requirement.** As high as possible. I want to be able to move this writing to a different host, a different domain, a different generator, with no migration work beyond rsyncing the files.

Now imagine storing all of that in a database with a CMS in front of it.

The single author is locked into one specific tool. The export path is whatever the CMS gives them. Migrating off requires writing a custom exporter, possibly losing formatting or metadata. The version history of any post is tied to the CMS's audit log instead of being a normal git diff. Drafts cannot be edited offline on a plane. Search-and-replace across the corpus requires a custom CMS query, not `sed`.

Worse: every dependency the CMS adds is a future risk to the durability of the writing. CMS gets discontinued? Database migration. CMS bumps a major version? Schema migration. CMS gets bought by a company that turns it into a SaaS? Re-migration, possibly under hostile terms. None of that is hypothetical; it has happened to every long-lived author who chose a managed CMS.

The right choice for a blog is flat files in a directory the author controls. Markdown is convention; the principle is "files." Plain HTML works. Org-mode works. Any text format you can read in twenty years with a text editor works. The point is that the content's home is a directory, and the directory's home is git, and git's home is wherever I push it next.

## The five-question diagnostic

Faced with a new content surface, before choosing a storage model, run the access pattern past five questions.

**1. How many writers will touch a record at the same time?**

If the answer is one person at a time, files are fine. If the answer is many writers simultaneously, you need a database with concurrency control.

**2. Are records mutated in-place after creation, or grown by appending?**

If records are essentially immutable once written (a blog post), files are great. If records are constantly mutated (status flags, reaction counts, edit history), files are bad — every mutation is a commit, and the commit history loses signal.

**3. Are reads dominated by single-record lookups or by list operations?**

Single-record lookups are file-friendly: the URL maps to a path, the path holds the file, render it. List operations are database-friendly: the index, the search query, the sorted feed all want indexes the database already has.

**4. How long does the content need to survive the platform?**

Short-shelf-life content tolerates platform lock-in. Long-shelf-life content needs to be portable, which means the format has to be open and the storage has to be transferable. Files win this category by default.

**5. How important is offline editing and ad-hoc tooling?**

If the answer is "very important," files win again. A directory of markdown files works with every text editor, every diff tool, every search tool, every static analysis tool. A database requires whatever the CMS offers, plus whatever you build to extend it.

Each question pushes you toward one model or the other. The answers usually cluster cleanly. When they cluster *toward database*, you have a database surface. When they cluster *toward files*, you have a files surface. When they cluster mixed, you almost always actually have *two surfaces* dressed up as one, and you should split them.

## When you have both, split them

The interesting case is when one product needs both kinds of surface.

A typical example: a SaaS app where customers post short-form messages in real time (community feed) but also publish long-form articles (personal pages). The temptation is to put both in the database because "well, the community is in the database, just put the articles there too." Or, less often, to put both in files because "well, the articles are in files, just put the community there too."

Both lead to misery. The community-in-files version cannot handle write concurrency. The articles-in-database version makes the article writers fight the CMS forever and prevents portability.

The right answer is two storage subsystems behind one product surface. The community uses the database. The articles use files. The frontend joins them at render time. Each storage layer is right for its own workload. Splitting feels redundant; running them merged feels coherent. The redundant version is the correct one.

The cost is a small amount of integration code and the discipline to maintain two systems instead of one. The benefit is that each surface uses a storage model that matches its access pattern, and neither surface is paying the cost of the other's tradeoffs.

## Why the default choice is wrong so often

Most teams have a default storage model. It is whichever the framework defaults to (a database) or whichever the team is most comfortable with (also usually a database). They apply it to every content surface they ship.

Most teams' content surfaces include at least one that is wrong for their default. Documentation sites. Marketing pages. Long-form articles. Any surface with one writer, mostly-immutable records, single-record reads, and a long durability horizon. Those surfaces want to be files. The team is using a database for them, and paying.

The cost is invisible because nobody benchmarks it. The marketing site nobody can edit on a plane. The documentation that requires logging into a CMS to fix a typo. The articles that get accidentally deleted in a database migration. The author who wants to leave the platform and discovers the export is a partial JSON dump that requires custom transformation.

These are the symptoms of a wrong default. The fix is to recognize per-surface what the access pattern is, and choose the storage model that matches.

## The summary, made dogmatic

A surface with many writers, mutable records, list-dominant reads, short-shelf-life content, and platform lock-in tolerance wants a database.

A surface with one writer, immutable records, single-record reads, long-shelf-life content, and portability requirements wants files.

When you have both kinds of surface, run them on two storage layers. Do not let one default eat the other.

Most teams choose once and pay forever. You do not have to be one of them.
