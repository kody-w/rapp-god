---
layout: post
title: "Static Sites Are the Right Default for Personal Infrastructure"
date: 2026-04-18
tags: [static-sites, infrastructure, defaults, hosting, architecture]
---

If you are building infrastructure for yourself — a personal site, a personal tool, a personal twin of some platform — the right default is a static site. Not a server. Not a serverless function. Not a managed app platform. A folder of HTML, CSS, and JavaScript files served by a web server you don't operate.

The reasoning is about lifecycle costs, not capability. Static sites can do almost anything a dynamic site can do. The dynamic side just costs more, in dimensions that compound over years.

**Hosting cost.** A static site on GitHub Pages, Netlify, Cloudflare Pages, or any CDN is free or close to free at any scale a personal project will ever reach. A dynamic site requires a server. A server requires a billing relationship. A billing relationship requires attention — credit card updates, invoice review, capacity planning. Over a decade, the cumulative attention is significant. Static sites deduct this cost to zero.

**Operational cost.** A static site does not crash. It does not run out of memory. It does not need restarts. It does not have a process to monitor. Its uptime is the uptime of the CDN, which is higher than any uptime you can engineer yourself. A dynamic site requires you to be on call for it, even if quietly. Static sites delete the on-call burden entirely.

**Security cost.** A static site has no attack surface beyond the file contents. There is no SQL injection because there is no SQL. There is no auth bypass because there is no auth. There is no remote code execution because there is no execution at all on the server side. The only thing a static site can leak is what's already in the repo. A dynamic site has many more failure modes, each of which has to be defended.

**Cognitive cost.** A static site is comprehensible end-to-end by one person. The sources are files in a repo. The build is a script you can read in fifteen minutes. The output is files in a folder. There is nothing magical happening at runtime. A dynamic site has runtime behavior that is not obvious from the source — request handling, session state, database queries, cache invalidation. Each of those is a thing you have to keep in your head.

**Forkability.** A static site can be forked in literal seconds. Clone the repo, run the build script, deploy to any CDN. The new fork is fully independent. A dynamic site requires you to also reproduce the runtime environment, which is much harder. Static sites are maximally portable; dynamic sites are minimally portable.

The standard objection is "but I need dynamic features — auth, comments, real-time updates, personalization." Almost always, those features can be sliced into a small set of API calls handled by a single function or a third-party service, while the bulk of the site stays static. The pattern is: static-first, with surgical dynamism only where it's required.

Concrete patterns I've leaned on:

- **GitHub Issues as a write API.** When users need to submit data, a labeled issue is a free, secure, audit-logged backend with a built-in moderation layer. The issue body is JSON. A workflow processes it.
- **GitHub Discussions as comments.** When you need conversations on a piece of content, a Discussion thread provides the storage, the UI, the authentication, the rate limiting, and the moderation. You don't build any of it.
- **Cloudflare Workers for OAuth.** When you need a token exchange, a single fifty-line worker handles it. No server. No database. The worker exists only for the duration of one HTTP request.
- **Read-only SDKs.** When you need to expose your data programmatically, ship a single-file SDK that reads from `raw.githubusercontent.com`. The repo is the API.

These patterns combine into a stack where the static site does the rendering, the CDN does the serving, GitHub does the storage and write path, and a tiny worker handles the cases that genuinely require server-side computation. The total operational burden is approximately zero.

Static sites are not the right default for everything. They are the right default for *personal* infrastructure — projects you own, projects without a customer SLA, projects where you are the only operator. Within that scope, the cost-benefit ratio is so lopsided that "is this static-first" should be the question you ask before you write any code.

Choose static. Pay the small upfront design cost. Avoid the perpetual operational cost.
