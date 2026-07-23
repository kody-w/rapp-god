# Copilot Instructions

## Architecture

This is a Jekyll blog hosted on GitHub Pages. There is no build step beyond what GitHub Pages runs automatically — no Gemfile, no local bundler config, no CI pipeline.

- **`_config.yml`** — Site metadata. Uses kramdown for Markdown and rouge for syntax highlighting. Permalink pattern: `/:year/:month/:day/:title/`.
- **`_layouts/default.html`** — Base HTML shell (header, nav, footer). All pages inherit from this.
- **`_layouts/post.html`** — Wraps `default.html`, adds post title and date. Used by all blog posts.
- **`css/main.css`** — Single stylesheet for the entire site. Blog styles plus portfolio card/grid styles for the About page.
- **`about.md`** — Portfolio page with project cards, features grid, and social links. Uses raw HTML inside Markdown (not Markdown syntax) for the card layout.
- **`index.html`** — Homepage. Lists all posts using a Liquid `{% for post in site.posts %}` loop.
- **`feed.xml`** — Atom feed generated with Liquid.

## Blog Post Conventions

Posts live in `_posts/` and must follow Jekyll's naming convention: `YYYY-MM-DD-slug-title.md`.

Every post uses this front matter exactly:

```yaml
---
layout: post
title: "Post Title Here"
date: YYYY-MM-DD
---
```

No categories, tags, or other front matter fields are used. Posts are plain Markdown (kramdown) with no custom Liquid tags or shortcodes.

## Styling

The theme is a minimal, Karpathy-inspired design. Key design tokens in `css/main.css`:

- Max content width: `800px` (via `.wrap`)
- Primary color: `#2a7ae2`
- Font stack: `-apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif`
- Border accent: `5px solid #333` top border on header

The About page uses additional component styles (`.cards`, `.stats`, `.features-grid`, `.social-links`) that are all in the same `main.css` file. Font Awesome 6.4 is loaded from CDN for icons on the About page.
