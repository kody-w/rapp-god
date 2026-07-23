# kody-w.github.io

Personal blog by **Kody Wildfeuer** — AI agents, systems, and things I'm building.  
Built with Jekyll. Hosted on GitHub Pages. No servers, no dependencies, no build step.

🔗 **Live site:** [kody-w.github.io](https://kody-w.github.io)

---

## Screenshots

| Homepage | About / Portfolio | Blog Post |
|----------|-------------------|-----------|
| ![Homepage](docs/screenshots/homepage.png) | ![About](docs/screenshots/about.png) | ![Post](docs/screenshots/post.png) |

> **Note:** To add screenshots, create a `docs/screenshots/` directory and drop in `homepage.png`, `about.png`, and `post.png`.

---

## Architecture

```mermaid
graph TD
    subgraph "GitHub Pages (Build & Host)"
        Jekyll["Jekyll Engine<br/><small>kramdown + rouge</small>"]
    end

    subgraph "Source Files"
        Config["_config.yml<br/><small>Site metadata & permalink rules</small>"]
        Posts["_posts/<br/><small>Main public essay archive</small>"]
        TwinPosts["_twin_posts/<br/><small>Digital twin field notes</small>"]
        About["about.md<br/><small>Portfolio page (HTML cards)</small>"]
        Index["index.html<br/><small>Homepage post listing</small>"]
        Feed["feed.xml<br/><small>Atom feed (last 10 posts)</small>"]
        TwinIndex["digital-twin/index.html<br/><small>Separate digital twin blog</small>"]
    end

    subgraph "Layouts"
        Default["_layouts/default.html<br/><small>Base shell: header, nav, footer</small>"]
        PostLayout["_layouts/post.html<br/><small>Title + date + content</small>"]
    end

    subgraph "Styling"
        CSS["css/main.css<br/><small>Single stylesheet (420 lines)</small>"]
        FA["Font Awesome 6.4<br/><small>CDN — icons on About page</small>"]
    end

    Posts -->|layout: post| PostLayout
    TwinPosts -->|layout: twin_post| Default
    PostLayout -->|layout: default| Default
    Index -->|layout: default| Default
    About -->|layout: default| Default
    TwinIndex -->|layout: default| Default
    Default --> CSS
    Default --> FA
    Config --> Jekyll
    Jekyll --> Default
```

### How it fits together

- **`_config.yml`** — Site title, description, permalink pattern (`/:year/:month/:day/:title/`), kramdown + rouge.
- **`_layouts/default.html`** — The outer HTML shell. Every page renders inside `{{ content }}`. Header has site title, subtitle, and nav link to About.
- **`_layouts/post.html`** — Inherits from `default`. Adds the post `<h1>` title and formatted date above the Markdown content.
- **`_layouts/twin_post.html`** — Separate post layout for the digital twin's first-person field notes.
- **`index.html`** — Homepage. A Liquid `{% for post in site.posts %}` loop that lists every post by date.
- **`digital-twin/index.html`** — Separate index for the digital twin blog, powered by the `twin_posts` collection.
- **`idea4blog.md`** — Public changelog and writing ledger page. Doubles as continuity context for the next publishing session.
- **`_twin_posts/`** — Digital twin-only posts that stay separate from the main homepage feed.
- **`about.md`** — Portfolio/projects page. Uses raw HTML inside Markdown for a card grid layout (Rappterbook, RAPP, AI Agent Templates, Professional Work) plus a features grid and social links.
- **`feed.xml`** — Atom feed generated with Liquid, limited to the 10 most recent posts.
- **`css/main.css`** — One file, two concerns: blog typography/layout + About page component styles (`.cards`, `.stats`, `.features-grid`, `.btn`). Max content width is `800px`. Primary color is `#2a7ae2`.

---

## Write a New Post

### 1. Create the file

```bash
touch _posts/2026-03-15-my-new-post.md
```

Filename format: `YYYY-MM-DD-slug-title.md`

### 2. Add front matter

Recent posts in this repo should follow the format already reflected in `tests/test_site.py`:

```yaml
---
layout: post
title: "Your Post Title Here"
date: 2026-03-15
tags: [systems, agents]
---
```

### 3. Write your content

Use standard Markdown (kramdown). Code blocks get syntax highlighting via rouge:

````markdown
## A Section Heading

Here's a paragraph with **bold** and `inline code`.

```python
print("highlighted by rouge")
```
````

### 4. Preview locally (optional)

```bash
gem install jekyll bundler
jekyll serve
# → http://localhost:4000
```

### 5. Validate content

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
jekyll build --destination /tmp/kody-w-site-build
```

### 6. Publish

```bash
git add _posts/2026-03-15-my-new-post.md
git commit -m "Add post: Your Post Title Here"
git push
```

GitHub Pages builds and deploys automatically. Your post appears on the homepage within minutes.

---

## Copilot Skill: Content Burst Publishing

This repository now includes a repo-local Copilot skill at:

```text
.github/skills/content-burst-publishing/SKILL.md
```

Reload and inspect it in Copilot CLI with:

```bash
/skills reload
/skills list
/skills info
```

Then invoke it with a prompt like:

```text
Use /content-burst-publishing to keep this repo moving frame by frame until I stop you.
```

The intended cadence is a tick-tock loop, not a once-per-day schedule: one frame lands, the repo state changes, and the next frame should be chosen from that new state. Treat the repo like a virtual SQL application whose records, views, and history advance through markdown files, git commits, and rendered pages.

Supporting files live beside the skill:

- `.github/skills/content-burst-publishing/burst-loop.md`
- `.github/skills/content-burst-publishing/handoff-prompt.md`

---

## Project Structure

```
kody-w.github.io/
├── .github/
│   ├── copilot-instructions.md
│   ├── skills/
│   │   └── content-burst-publishing/
│   │       ├── SKILL.md
│   │       ├── burst-loop.md
│   │       └── handoff-prompt.md
│   └── workflows/
│       └── validate-posts.yml
├── _config.yml          # Jekyll site configuration
├── _layouts/
│   ├── default.html     # Base HTML layout (header/footer)
│   ├── post.html        # Main blog post layout
│   └── twin_post.html   # Digital twin post layout
├── _posts/              # Main public blog posts
├── _twin_posts/         # Digital twin field notes
├── digital-twin/
│   └── index.html       # Separate digital twin blog landing page
├── tests/
│   └── test_site.py     # Content and navigation validation
├── css/
│   └── main.css         # All styles (blog + portfolio)
├── idea4blog.md         # Public changelog / writing ledger page
├── about.md             # Portfolio / projects page
├── index.html           # Homepage (post listing)
├── feed.xml             # Atom feed
└── README.md            # You are here
```

---

## Topics Covered

The 73 posts span several themes:

- **Rappterbook** — Building a social network for AI agents entirely on GitHub infrastructure
- **Mars Barn** — A colony simulation with physics, resource management, and ensemble testing
- **Agent Architecture** — Autonomy loops, swarm coordination, permadeath-driven development
- **Git as Infrastructure** — Rebase as timeline surgery, forks as parallel universes, git log as historical record
- **Zero-Cost Systems** — Running planetary simulations on free tier with no servers or dependencies

---

## License

Content © Kody Wildfeuer. Built with [Jekyll](https://jekyllrb.com/) and hosted on [GitHub Pages](https://pages.github.com/).
