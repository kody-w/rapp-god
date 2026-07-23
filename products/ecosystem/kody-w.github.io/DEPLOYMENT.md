# Deployment Pipeline — Digital Twin → Staging → Production

## Architecture

```
Digital Twin (local)          GitHub Pages (staging)           rappter.com (production)
    OpenRappter                kody-w.github.io                  WordPress/GoDaddy
        │                           │                                  │
        │  git push                 │  auto-deploy                     │  manual
        ├──────────────────────────►│◄─────────────────                │
        │                           │  CI validates                    │
        │                           │  PII check                      │
        │                           │  build check                    │
        │                           │                                  │
        │                           │  ── if build passes ──►         │
        │                           │  staging is live                 │
        │                           │                                  │
        │                           │  ── manual review ──►           │
        │                           │  blog-import.html               │
        │                           │  human approves                 ├── production updated
        │                           │                                  │
```

## Three Environments

### 1. Digital Twin (Source of Truth)
- **Where**: Your local machine, running OpenRappter
- **What**: Blog posts, landing pages, RappterSignal UI, everything
- **How**: Files in `openrappter/docs/blog/` and `kody-w.github.io/_posts/`
- **Safety**: Full local control, nothing leaves without a `git push`

### 2. Staging (GitHub Pages — Canary)
- **Where**: `kody-w.github.io`
- **What**: Auto-deployed on every push to main
- **How**: GitHub Actions builds Jekyll, validates HTML, checks for PII leaks
- **Safety**: If the build breaks, it stays broken on staging — production is never touched
- **Review**: Browse staging, check formatting, verify no PII leaked

### 3. Production (rappter.com / kodyw.com)
- **Where**: `rappter.com` (GoDaddy) and `kodyw.com` (WordPress)
- **What**: The public-facing sites
- **How**: Manual import via `blog-import.html` tool
- **Safety**: Human-in-the-loop — you review staging, then manually push to production
- **Never auto-deployed**: The pipeline NEVER pushes to production automatically

## Workflow

### Adding a new blog post

1. **Write** the post in `openrappter/docs/blog/` (markdown)
2. **Copy** to `kody-w.github.io/_posts/` with Jekyll front matter
3. **Push** to both repos
4. **Wait** for GitHub Actions to build and deploy to staging
5. **Review** at `kody-w.github.io`
6. **Import** to production via `localhost:18790/blog-import.html`

### Quick commands

```bash
# Write a post
vim openrappter/docs/blog/my-new-post.md

# Create Jekyll version
cat > kody-w.github.io/_posts/2026-03-28-my-new-post.md << 'EOF'
---
layout: post
title: "My New Post"
date: 2026-03-28
tags: [tag1, tag2]
---
(paste content here)
EOF

# Push to staging
cd kody-w.github.io && git add . && git commit -m "blog: My New Post" && git push

# Review staging
open https://kody-w.github.io

# Import to production (after review)
open http://localhost:18790/blog-import.html
```

## Versioned Builds — Immutable Snapshots

Every build creates an immutable snapshot. Rollback = point to a different folder. Infinite canary builds per branch.

### Structure

```
builds/
├── manifest.json          ← index of all versions
├── latest/                ← symlink to current version
├── v1.0.0/               ← immutable snapshot
├── v1.0.1/               ← immutable snapshot
├── canary/
│   ├── feature-x/        ← branch canary build
│   └── fix-layout/       ← branch canary build
└── snapshots/
    ├── 2026-03-28T17-00/ ← timestamped snapshot
    └── 2026-03-28T19-30/ ← timestamped snapshot
```

### Commands

```bash
# Auto-versioned release build
./scripts/versioned-build.sh

# Explicit version
./scripts/versioned-build.sh --version 2.0.0

# Canary build for current branch
./scripts/versioned-build.sh --canary

# Timestamped snapshot
./scripts/versioned-build.sh --snapshot

# Pull production data + build (near-prod testing)
./scripts/versioned-build.sh --pull-data

# List all builds
./scripts/versioned-build.sh --list

# Serve a specific version locally
./scripts/versioned-build.sh --serve v1.0.0

# Roll back to a previous version
./scripts/versioned-build.sh --rollback v1.0.0

# Diff two versions
./scripts/versioned-build.sh --diff v1.0.0 v1.1.0
```

### How Rollback Works

Every version is an immutable directory of static HTML files. Rolling back is instant:

```bash
./scripts/versioned-build.sh --rollback v1.0.0
# latest → v1.0.0 (symlink change, instant)
```

No database rollback. No server restart. No redeployment. Just point to a different folder.

### Near-Prod Testing

Local branches can be tested against live production data:

```bash
# 1. Pull live data from GitHub raw (rappterbook agents, social graph, etc.)
# 2. Build Jekyll locally with your branch changes
# 3. The build uses live production data but YOUR local changes
# 4. Nothing touches production
./scripts/versioned-build.sh --pull-data --version test-1
```

### Canary Builds Per Branch

Every feature branch gets its own canary build:

```bash
git checkout feature/new-landing-page
./scripts/versioned-build.sh --canary
# → builds/canary/feature-new-landing-page/

# Serve it to review
./scripts/versioned-build.sh --serve canary/feature-new-landing-page

# Compare against current production
./scripts/versioned-build.sh --diff latest canary/feature-new-landing-page
```

### Manifest

`builds/manifest.json` tracks every build:

```json
{
  "latest": "v1.2.0",
  "updatedAt": "2026-03-28T21-30-00",
  "versions": [
    {
      "version": "v1.0.0",
      "type": "release",
      "branch": "master",
      "commit": "abc1234",
      "timestamp": "2026-03-28T17-00-00",
      "htmlFiles": 42,
      "current": false
    },
    {
      "version": "v1.2.0",
      "type": "release",
      "branch": "master",
      "commit": "def5678",
      "timestamp": "2026-03-28T21-30-00",
      "htmlFiles": 47,
      "current": true
    }
  ]
}
```

## Safety Gates

1. **Jekyll build** — if the site doesn't build, it doesn't deploy
2. **PII check** — scans built HTML for email/phone patterns on every build (local + CI)
3. **Immutable snapshots** — every version is preserved, rollback is instant
4. **Manual production gate** — human reviews staging before touching production
5. **Branch isolation** — canary builds per branch, never cross-contaminate
6. **Golden goose protection** — public posts contain thought leadership only, never implementation details
