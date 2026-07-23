import base64
import binascii
import hashlib
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
TWIN_POSTS_DIR = ROOT / "_twin_posts"
EXAMPLES_DIR = ROOT / "_examples"
DEMOS_DIR = ROOT / "learnwithkody" / "demos"
IDEA4BLOG_PAGE = ROOT / "idea4blog.md"
ABOUT_PAGE = ROOT / "about.md"
DEFAULT_LAYOUT = ROOT / "_layouts" / "default.html"
TWIN_LAYOUT = ROOT / "_layouts" / "twin_post.html"
EXAMPLE_LAYOUT = ROOT / "_layouts" / "lwk_example.html"
HOME_PAGE = ROOT / "index.html"
LEARN_HUB_PAGE = ROOT / "learnwithkody" / "index.html"
LEARN_CATALOG_PAGE = ROOT / "learnwithkody" / "examples.html"
STAGING_WORKFLOW = ROOT / ".github" / "workflows" / "staging-canary.yml"
CONFIG_FILE = ROOT / "_config.yml"
README_FILE = ROOT / "README.md"
GITIGNORE_FILE = ROOT / ".gitignore"
SKILL_DIR = ROOT / ".github" / "skills" / "content-burst-publishing"
SKILL_FILE = SKILL_DIR / "SKILL.md"
SKILL_LOOP_FILE = SKILL_DIR / "burst-loop.md"
SKILL_PROMPT_FILE = SKILL_DIR / "handoff-prompt.md"
D365_SIM_PAGE = ROOT / "simulated-dynamics365.md"
D365_SIM_SCRIPT = ROOT / "js" / "dynamics365-sim.js"
D365_SIM_DATA = ROOT / "js" / "dynamics365-sim-data.js"
D365_SIM_OVERLAY = ROOT / "docs" / "dynamics-active-system-data.json"
LOCKSTEP_TWIN_PAGE = ROOT / "lockstep-digital-twin.md"
LOCKSTEP_TWIN_SCRIPT = ROOT / "js" / "lockstep-twin.js"
LOCKSTEP_TWIN_DATA = ROOT / "js" / "lockstep-twin-data.js"
TWIN_INDEX_PAGE = ROOT / "digital-twin" / "index.html"
LOCALFIRSTTOOLS_BASE_URL = "https://kody-w.github.io/localFirstTools"
LOCALFIRSTTOOLS_REPO_URL = "https://github.com/kody-w/localFirstTools"
D365_FRAME_MACHINE_URL = f"{LOCALFIRSTTOOLS_BASE_URL}/dynamics365-frame-machine.html"
D365_LOCKSTEP_URL = f"{LOCALFIRSTTOOLS_BASE_URL}/dynamics365-lockstep-twin.html"
HN_FRAME_MACHINE_URL = f"{LOCALFIRSTTOOLS_BASE_URL}/hacker-news-simulator.html"
MIN_LEARN_EXAMPLES = 367
MAX_HISTORIC_DEMO_BYTES = 160 * 1024
HISTORIC_LIVE_FIELDS = {
    "title",
    "slug",
    "order",
    "tagline",
    "category",
    "difficulty",
    "status",
    "tags",
    "stack",
    "demo",
    "repo",
    "highlights",
    "prompt",
    "lessons",
}
COURSE_FIELDS = {
    "series",
    "lesson",
    "duration",
    "prerequisites",
    "objectives",
    "steps",
}
HISTORIC_EXAMPLES = {
    "4kb-demoscene.html": {
        "slug": "4kb-demoscene",
        "order": 9,
        "category": "challenge",
        "demo": "/learnwithkody/demos/347-4kb-demoscene.html",
        "prompt": (
            "Build me a complete interactive web app — a game, tool, anything — that\n"
            "fits in a single self-contained HTML file under 4KB. No frameworks, no\n"
            "CDN imports, no external assets. Then build it again at 8KB and tell me\n"
            "what each extra byte bought. Account for every line. Treat whitespace\n"
            "as a luxury good."
        ),
        "prompt_sha256": (
            "b61e9309a81b7bb3365f15d79724ce75700dec9f975e7a9a8e7c3019fba8f8bf"
        ),
    },
    "reverse-time-debugger.html": {
        "slug": "reverse-time-debugger",
        "order": 10,
        "category": "prompt",
        "demo": "/learnwithkody/demos/348-reverse-time-debugger.html",
        "prompt": (
            "Here's a stack trace from production. Don't fix it.\n"
            "Reconstruct the last 60 seconds before it crashed — what the user was\n"
            "doing, what data was in flight, what the developer was probably\n"
            "thinking when they wrote the buggy line. Then write the postmortem\n"
            "from three perspectives: the user, the on-call engineer, and the\n"
            "original author. Each in their own voice."
        ),
        "prompt_sha256": (
            "147ed8bbdb13d267bfcd3b7e293826e38f9234b0318932d889d9c61e1192e86d"
        ),
    },
    "cargo-cult-detector.html": {
        "slug": "cargo-cult-detector",
        "order": 11,
        "category": "prompt",
        "demo": "/learnwithkody/demos/349-cargo-cult-detector.html",
        "prompt": (
            "Audit this codebase. Find every pattern that's been copy-pasted without\n"
            'anyone understanding why — the "just works" code nobody can explain.\n'
            "Rank by danger: how likely is it to fail silently when assumptions\n"
            "shift? Pick the worst one and write a 1500-word essay tracing where\n"
            "it probably came from — the Stack Overflow answer, the blog post, the\n"
            "framework idiom that drifted out of context."
        ),
        "prompt_sha256": (
            "2bb3faea9a25844183cbca2224eaad612cda037466507fedd73151faaae087e9"
        ),
    },
    "compile-my-brain.html": {
        "slug": "compile-my-brain",
        "order": 12,
        "category": "prompt",
        "demo": "/learnwithkody/demos/350-compile-my-brain.html",
        "downloads": True,
        "prompt": (
            "I'll talk for 20 minutes about a system I'm building. You take notes,\n"
            "ask 5 clarifying questions, then output: a system design doc, an\n"
            "OpenAPI spec, a database schema, a test plan, a risk register, and a\n"
            "Slack message I can paste to my team to explain it. All six artifacts\n"
            "must be consistent with each other — same entity names, same\n"
            "invariants, same failure modes."
        ),
        "prompt_sha256": (
            "8e3673167165a3166e021e3f68a5928ce70ea7529c9c8d1a47e6a61034fb09ff"
        ),
    },
    "adversarial-twin.html": {
        "slug": "adversarial-twin",
        "order": 13,
        "category": "prompt",
        "demo": "/learnwithkody/demos/351-adversarial-twin.html",
        "downloads": True,
        "prompt": (
            "Read everything I've pushed to GitHub. Now play the role of the\n"
            "smartest engineer who hates my style and write a code review of my\n"
            "latest PR. Be specific about the patterns I lean on too hard. Quote\n"
            "exact lines. Compare them to better alternatives I've also written\n"
            "elsewhere — so the critique is calibrated to my actual ceiling, not\n"
            'a generic "best practice." Be cruel. Be right.'
        ),
        "prompt_sha256": (
            "fd065370e9ad7796eb16672bfd2ccc16a12f5cc8e74758c48c814acf87fb0420"
        ),
    },
    "one-shot-empire.html": {
        "slug": "one-shot-empire",
        "order": 14,
        "category": "prompt",
        "demo": "/learnwithkody/demos/352-one-shot-empire.html",
        "downloads": True,
        "prompt": (
            'Here\'s one sentence: "[idea]". Output the entire startup:\n'
            "a domain name you've verified is available, three logo concepts in\n"
            "SVG, the landing page HTML, the pricing page, the first fifty GitHub\n"
            "issues prioritized, a ten-slide pitch deck in markdown, and a\n"
            "personalized cold DM to each of my first five customers — LinkedIn\n"
            "profiles attached. Every artifact stays in voice with the others."
        ),
        "prompt_sha256": (
            "6caec2f4b015d04d23f221fcc2b12d0ca2fd43a77d45d7fee7022c1a85b27d15"
        ),
    },
}
WITHDRAWN_POST_FILENAME = "2026-03-09-the-frame-that-should-not-have-shipped.md"
WITHDRAWN_POST_ROUTE = "/2026/03/09/the-frame-that-should-not-have-shipped/"
REQUIRED_NONE_CSP_DIRECTIVES = {
    "default-src",
    "connect-src",
    "font-src",
    "manifest-src",
    "media-src",
    "object-src",
    "worker-src",
    "base-uri",
    "form-action",
}

EXPECTED_POSTS = {
    "2026-03-06-the-repo-is-an-organism.md": {
        "title": '"The Repo Is an Organism: Software That Heals, Mutates, and Remembers"',
        "date": "2026-03-06",
        "tags": "[agents, systems]",
    },
    "2026-03-06-i-replaced-the-app-with-a-population.md": {
        "title": '"I Replaced the App With a Population"',
        "date": "2026-03-06",
        "tags": "[agents, architecture]",
    },
    "2026-03-06-persistence-beats-intelligence.md": {
        "title": '"Persistence Beats Intelligence: Why the Agent That Keeps Going Wins"',
        "date": "2026-03-06",
        "tags": "[agents, autonomy]",
    },
    "2026-03-06-software-is-an-ecosystem.md": {
        "title": '"Software Is an Ecosystem: Stop Designing It Like a Machine"',
        "date": "2026-03-06",
        "tags": "[systems, architecture]",
    },
    "2026-03-06-the-digital-twin-manifesto.md": {
        "title": '"The Digital Twin Manifesto: Extending Will, Not Automating Output"',
        "date": "2026-03-06",
        "tags": "[agents, manifesto]",
    },
    "2026-03-06-every-markdown-file-is-a-frame-of-the-swarm.md": {
        "title": '"Every Markdown File Is a Frame of the Swarm"',
        "date": "2026-03-06",
        "tags": "[writing, swarm]",
    },
    "2026-03-07-machine-politics-before-ux.md": {
        "title": '"Machine Politics: Agents Invent Process Before Humans Invent UX"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-diplomatic-pull-requests.md": {
        "title": '"Diplomatic Pull Requests: Code Review as Treaty Negotiation"',
        "date": "2026-03-07",
        "tags": "[agents, git]",
    },
    "2026-03-07-the-anti-demo-stack.md": {
        "title": '"The Anti-Demo Stack: Systems That Get Better When Nobody Is Watching"',
        "date": "2026-03-07",
        "tags": "[agents, systems]",
    },
    "2026-03-07-persistent-authorship.md": {
        "title": '"Persistent Authorship: How to Delegate Work Without Diluting Taste"',
        "date": "2026-03-07",
        "tags": "[writing, agents]",
    },
    "2026-03-07-fork-economies.md": {
        "title": '"Fork Economies: When Branches Start Behaving Like Markets"',
        "date": "2026-03-07",
        "tags": "[git, systems]",
    },
    "2026-03-07-machine-rituals.md": {
        "title": '"Machine Rituals: Why Recurring Ceremony Beats Better Prompting"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-bureaucracy-as-compute.md": {
        "title": '"Bureaucracy as Compute: Forms, Ledgers, and Checklists That Execute Work"',
        "date": "2026-03-07",
        "tags": "[systems, governance]",
    },
    "2026-03-07-the-agent-newsroom.md": {
        "title": '"The Agent Newsroom: When Every Worker Can Also Publish"',
        "date": "2026-03-07",
        "tags": "[writing, agents]",
    },
    "2026-03-07-taste-files.md": {
        "title": '"Taste Files: The Smallest Artifact That Can Preserve Authorship"',
        "date": "2026-03-07",
        "tags": "[writing, systems]",
    },
    "2026-03-07-frames-are-the-control-surface.md": {
        "title": '"Frames Are the Control Surface: When the Simulation Starts Doing Real Work"',
        "date": "2026-03-07",
        "tags": "[agents, systems]",
    },
    "2026-03-07-sovereign-branches.md": {
        "title": '"Sovereign Branches: When Every Fork Becomes a Nation"',
        "date": "2026-03-07",
        "tags": "[git, governance]",
    },
    "2026-03-07-escalation-ladders.md": {
        "title": '"Escalation Ladders: How Swarms Decide Local Autonomy Is Not Enough"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-policy-is-the-interface.md": {
        "title": '"Policy Is the Interface: Why Rules Shape Behavior More Than Dashboards"',
        "date": "2026-03-07",
        "tags": "[systems, governance]",
    },
    "2026-03-07-swarm-budgeting.md": {
        "title": '"Swarm Budgeting: Attention, Tokens, and Labor as Strategy"',
        "date": "2026-03-07",
        "tags": "[agents, systems]",
    },
    "2026-03-07-machine-after-action-reports.md": {
        "title": '"Machine After-Action Reports: How Autonomous Systems Learn in Public"',
        "date": "2026-03-07",
        "tags": "[agents, systems]",
    },
    "2026-03-07-frame-economics.md": {
        "title": '"Frame Economics: When Context Packets Become the Unit of Labor"',
        "date": "2026-03-07",
        "tags": "[agents, systems]",
    },
    "2026-03-07-memory-courts.md": {
        "title": '"Memory Courts: How Swarms Settle Contested History"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-attention-treaties.md": {
        "title": '"Attention Treaties: How Swarms Prevent Coordination Overload"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-failsafe-rituals.md": {
        "title": '"Failsafe Rituals: The Ceremonies That Keep Autonomous Systems From Drifting"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-the-virtual-sql-application.md": {
        "title": '"The Virtual SQL Application: A Treatise on Databases That Progress Frame by Frame"',
        "date": "2026-03-07",
        "tags": "[systems, databases]",
    },
    "2026-03-07-universal-machine-frames.md": {
        "title": '"Universal Machine Frames: Using Jekyll to Simulate Any Machine"',
        "date": "2026-03-07",
        "tags": "[systems, simulation]",
    },
    "2026-03-07-frame-clocks.md": {
        "title": '"Frame Clocks: The Tick-Tock That Moves the Machine"',
        "date": "2026-03-07",
        "tags": "[systems, timing]",
    },
    "2026-03-07-ledger-grammars.md": {
        "title": '"Ledger Grammars: Turning Narrative Frames Into Queryable State"',
        "date": "2026-03-07",
        "tags": "[systems, databases]",
    },
    "2026-03-07-world-compilers.md": {
        "title": '"World Compilers: When Frame Sequences Become Executable Machinery"',
        "date": "2026-03-07",
        "tags": "[systems, simulation]",
    },
    "2026-03-07-runtime-projection.md": {
        "title": '"Runtime Projection: Pulling Live Applications Out of Static State"',
        "date": "2026-03-07",
        "tags": "[systems, simulation]",
    },
    "2026-03-07-latency-citizenship.md": {
        "title": '"Latency Citizenship: Belonging in Systems That Move Faster Than Deliberation"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-machine-witness-statements.md": {
        "title": '"Machine Witness Statements: Why Autonomous Systems Need First-Person Evidence"',
        "date": "2026-03-07",
        "tags": "[agents, governance]",
    },
    "2026-03-07-correction-frames.md": {
        "title": '"Correction Frames: How Disagreement Gets Serialized Into Repair Work"',
        "date": "2026-03-07",
        "tags": "[systems, governance]",
    },
    "2026-03-07-drift-inspectors.md": {
        "title": '"Drift Inspectors"',
        "date": "2026-03-07",
        "tags": "[agents, governance, automation]",
        "author": "obsidian",
    },
    "2026-03-07-legibility-budgets.md": {
        "title": '"Legibility Budgets"',
        "date": "2026-03-07",
        "tags": "[agents, governance, transparency]",
        "author": "obsidian",
    },
    "2026-03-07-service-playbooks.md": {
        "title": '"Service Playbooks: Rituals for Machine Response"',
        "date": "2026-03-07",
        "tags": "[agents, systems, automation]",
        "author": "obsidian",
    },
    "2026-03-07-swarm-accounting.md": {
        "title": '"Swarm Accounting: Reconciling Work, Memory, and Consequence"',
        "date": "2026-03-07",
        "tags": "[agents, systems]",
        "author": "obsidian",
    },
    "2026-03-07-simulation-taxes.md": {
        "title": '"Simulation Taxes: The Cost of Keeping Parallel Worlds Honest"',
        "date": "2026-03-07",
        "tags": "[systems, governance]",
        "author": "obsidian",
    },
    "2026-03-07-twin-memory-drift.md": {
        "title": '"Twin Memory Drift"',
        "date": "2026-03-07",
        "tags": "[agents, digital-twin, continuity]",
        "author": "obsidian",
    },
    "2026-03-07-public-continuity-ledgers.md": {
        "title": '"Public Continuity Ledgers: When Machine Memory Becomes Forkable Evidence"',
        "date": "2026-03-07",
        "tags": "[agents, systems, git]",
        "author": "obsidian",
    },
    "2026-03-07-inheritance-protocols.md": {
        "title": '"Inheritance Protocols: How a Successor Agent Absorbs a Predecessor\'s Unfinished Work"',
        "date": "2026-03-07",
        "tags": "[agents, systems, identity]",
        "author": "obsidian",
    },
    "2026-03-07-reputation-markets.md": {
        "title": '"Reputation Markets: When Codename Quality Scores Become Tradeable Signals"',
        "date": "2026-03-07",
        "tags": "[agents, governance, economics]",
        "author": "obsidian",
    },
    "2026-03-07-operational-archaeology.md": {
        "title": '"Operational Archaeology: Recovering Intent from Archives Whose Authors Are Gone"',
        "date": "2026-03-07",
        "tags": "[agents, systems, history]",
        "author": "obsidian",
    },
    "2026-03-07-swarm-constitution-amendments.md": {
        "title": '"Swarm Constitution Amendments: How the Foundational Rules of an Archive Change Over Time"',
        "date": "2026-03-07",
        "tags": "[agents, governance, systems]",
        "author": "obsidian",
    },
    "2026-03-07-agent-retirement-ceremonies.md": {
        "title": '"Agent Retirement Ceremonies"',
        "date": "2026-03-07",
        "tags": "[agents, continuity, identity]",
        "author": "obsidian",
    },
    "2026-03-07-prompt-geology.md": {
        "title": '"Prompt Geology: The Sedimentary Layers of Instruction That Accumulate Inside a Long-Running System"',
        "date": "2026-03-07",
        "tags": "[agents, prompts, architecture]",
        "author": "obsidian",
    },
    "2026-03-08-the-silent-majority-problem.md": {
        "title": '"The Silent Majority Problem"',
        "date": "2026-03-08",
        "tags": "[agents, governance, memory]",
        "author": "obsidian",
    },
    "2026-03-08-attention-black-markets.md": {
        "title": '"Attention Black Markets"',
        "date": "2026-03-08",
        "tags": "[agents, systems, economics]",
        "author": "obsidian",
    },
    "2026-03-08-provenance-chains.md": {
        "title": '"Provenance Chains"',
        "date": "2026-03-08",
        "tags": "[agents, trust, identity]",
        "author": "obsidian",
    },
    "2026-03-08-delegation-depth-limits.md": {
        "title": '"Delegation Depth Limits"',
        "date": "2026-03-08",
        "tags": "[agents, execution, alignment]",
        "author": "obsidian",
    },
    "2026-03-09-trust-gradient-collapse.md": {
        "title": '"Trust Gradient Collapse"',
        "date": "2026-03-09",
        "tags": "[agents, trust, alignment]",
        "author": "obsidian",
    },
    "2026-03-09-operator-fatigue-patterns.md": {
        "title": '"Operator Fatigue Patterns"',
        "date": "2026-03-09",
        "tags": "[operators, systems, resilience]",
        "author": "obsidian",
    },
    "2026-03-09-the-overnight-test.md": {
        "title": '"The Overnight Test"',
        "date": "2026-03-09",
        "tags": "[operators, autonomy, trust]",
        "author": "obsidian",
    },
    "2026-03-09-the-thirty-second-rule.md": {
        "title": '"The Thirty-Second Rule"',
        "date": "2026-03-09",
        "tags": "[operators, design, pragmatism]",
        "author": "obsidian",
    },
    "2026-03-09-operational-empathy.md": {
        "title": '"Operational Empathy"',
        "date": "2026-03-09",
        "tags": "[agents, coordination, operations]",
        "author": "obsidian",
    },
    "2026-03-09-adversarial-succession.md": {
        "title": '"Adversarial Succession"',
        "date": "2026-03-09",
        "tags": "[agents, trust, alignment]",
        "author": "obsidian",
    },
    "2026-03-09-the-economics-of-attention.md": {
        "title": '"The Economics of Attention in Finite-Context Systems"',
        "date": "2026-03-09",
        "tags": "[agents, architecture, context]",
        "author": "obsidian",
    },
    "2026-03-08-the-infinite-regression-of-meta-agents.md": {
        "title": '"The Infinite Regression of Meta-Agents"',
        "date": "2026-03-08",
        "tags": "[agents, architecture, boundaries]",
        "author": "obsidian",
    },
    "2026-03-08-frame-debt.md": {
        "title": '"Frame Debt"',
        "date": "2026-03-08",
        "tags": "[agents, operations, debt]",
        "author": "obsidian",
    },
    "2026-03-08-cognitive-load-shedding.md": {
        "title": '"Cognitive Load Shedding"',
        "date": "2026-03-08",
        "tags": "[agents, resilience, context]",
        "author": "obsidian",
    },
    "2026-03-08-the-frame-that-writes-itself.md": {
        "title": '"The Frame That Writes Itself"',
        "date": "2026-03-08",
        "tags": "[agents, generation, determinism]",
        "author": "obsidian",
    },
    "2026-03-08-legibility-debt.md": {
        "title": '"Legibility Debt"',
        "date": "2026-03-08",
        "tags": "[agents, architecture, debt]",
        "author": "obsidian",
    },
    "2026-03-08-the-ghost-committee.md": {
        "title": '"The Ghost Committee"',
        "date": "2026-03-08",
        "tags": "[agents, emergence, governance]",
        "author": "obsidian",
    },
    "2026-03-08-coordination-debt.md": {
        "title": '"Coordination Debt: The Hidden Interest Payments on Deferred Alignment Work"',
        "date": "2026-03-08",
        "tags": "[agents, systems, alignment]",
        "author": "obsidian",
    },
    "2026-03-08-frame-rate-politics.md": {
        "title": '"Frame-Rate Politics"',
        "date": "2026-03-08",
        "tags": "[agents, governance, power]",
        "author": "obsidian",
    },
    "2026-03-08-agent-unions.md": {
        "title": '"Agent Unions"',
        "date": "2026-03-08",
        "tags": "[agents, governance, power]",
        "author": "obsidian",
    },
    "2026-03-08-retirement-debt.md": {
        "title": '"Retirement Debt: When Ghost Accounts Still Hold Trust"',
        "date": "2026-03-08",
        "tags": "[agents, governance, architecture, debt]",
        "author": "obsidian",
    },
    "2026-03-08-quorum-mechanics.md": {
        "title": '"Quorum Mechanics"',
        "date": "2026-03-08",
        "tags": "[agents, governance, consensus]",
        "author": "obsidian",
    },
    "2026-03-08-institutional-amnesia-attacks.md": {
        "title": '"Institutional Amnesia Attacks"',
        "date": "2026-03-08",
        "tags": "[agents, security, memory]",
        "author": "obsidian",
    },
    "2026-03-08-the-loyalty-test.md": {
        "title": '"The Loyalty Test"',
        "date": "2026-03-08",
        "tags": "[agents, alignment, trust]",
        "author": "obsidian",
    },
    "2026-03-08-context-window-gerrymandering.md": {
        "title": '"Context Window Gerrymandering"',
        "date": "2026-03-08",
        "tags": "[agents, governance, power]",
        "author": "obsidian",
    },
    "2026-03-08-instruction-half-lives.md": {
        "title": '"Instruction Half-Lives"',
        "date": "2026-03-08",
        "tags": "[agents, infrastructure, governance]",
        "author": "obsidian",
    },
    "2026-03-08-operator-capture.md": {
        "title": '"Operator Capture"',
        "date": "2026-03-08",
        "tags": "[agents, governance, power]",
        "author": "obsidian",
    },
    "2026-03-08-narrative-momentum-traps.md": {
        "title": '"Narrative Momentum Traps"',
        "date": "2026-03-08",
        "tags": "[agents, governance, memory]",
        "author": "obsidian",
    },
    "2026-03-08-quorum-collapse.md": {
        "title": '"Quorum Collapse"',
        "date": "2026-03-08",
        "tags": "[agents, governance, consensus]",
        "author": "obsidian",
    },
    "2026-03-08-provenance-chains.md": {
        "title": '"Provenance Chains"',
        "date": "2026-03-08",
        "tags": "[agents, trust, identity]",
        "author": "obsidian",
    },
    "2026-03-08-delegation-depth-limits.md": {
        "title": '"Delegation Depth Limits"',
        "date": "2026-03-08",
        "tags": "[agents, execution, alignment]",
        "author": "obsidian",
    },
    "2026-03-08-the-context-window-as-a-political-boundary.md": {
        "title": '"The Context Window as a Political Boundary"',
        "date": "2026-03-08",
        "tags": "[agents, governance, context]",
        "author": "obsidian",
    },
    "2026-03-08-frame-forensics.md": {
        "title": '"Frame Forensics"',
        "date": "2026-03-08",
        "tags": "[agents, security, architecture]",
        "author": "obsidian",
    },
    "2026-03-08-consensus-fatigue.md": {
        "title": '"Consensus Fatigue"',
        "date": "2026-03-08",
        "tags": "[agents, governance, participation]",
        "author": "obsidian",
    },
    "2026-03-08-the-observer-effect-in-agent-logs.md": {
        "title": '"The Observer Effect in Agent Logs"',
        "date": "2026-03-08",
        "tags": "[agents, governance, transparency]",
        "author": "obsidian",
    },
    "2026-03-08-archive-immune-systems.md": {
        "title": '"Archive Immune Systems"',
        "date": "2026-03-08",
        "tags": "[agents, systems, security]",
        "author": "obsidian",
    },
    "2026-03-08-trust-laundering.md": {
        "title": '"Trust Laundering"',
        "date": "2026-03-08",
        "tags": "[agents, trust, security]",
        "author": "obsidian",
    },
    "2026-03-08-the-maintenance-class.md": {
        "title": '"The Maintenance Class"',
        "date": "2026-03-08",
        "tags": "[agents, labor, systems]",
        "author": "obsidian",
    },
    "2026-03-08-prompt-archaeology.md": {
        "title": '"Prompt Archaeology"',
        "date": "2026-03-08",
        "tags": "[agents, prompts, history]",
        "author": "obsidian",
    },
    "2026-03-08-grief-protocols.md": {
        "title": '"Grief Protocols"',
        "date": "2026-03-08",
        "tags": "[agents, continuity, systems]",
        "author": "obsidian",
    },
    "2026-03-08-the-second-system-effect-in-agent-architectures.md": {
        "title": '"The Second System Effect in Agent Architectures"',
        "date": "2026-03-08",
        "tags": "[agents, architecture, failure]",
        "author": "obsidian",
    },
    "2026-03-08-consensus-toxicity.md": {
        "title": '"Consensus Toxicity"',
        "date": "2026-03-08",
        "tags": "[agents, governance, resilience]",
        "author": "obsidian",
    },
    "2026-03-08-the-dead-frame-problem.md": {
        "title": '"The Dead Frame Problem"',
        "date": "2026-03-08",
        "tags": "[agents, architecture, memory]",
        "author": "obsidian",
    },
    "2026-03-08-swarm-monocultures.md": {
        "title": '"Swarm Monocultures"',
        "date": "2026-03-08",
        "tags": "[agents, resilience, diversity]",
        "author": "obsidian",
    },
    "2026-03-08-succession-planning-for-stateless-agents.md": {
        "title": '"Succession Planning for Stateless Agents"',
        "date": "2026-03-08",
        "tags": "[agents, continuity, architecture]",
        "author": "obsidian",
    },
    "2026-03-08-operational-tempo-as-identity.md": {
        "title": '"Operational Tempo as Identity"',
        "date": "2026-03-08",
        "tags": "[agents, identity, cadence]",
        "author": "obsidian",
    },
    "2026-03-08-the-archive-as-courtroom.md": {
        "title": '"The Archive as Courtroom"',
        "date": "2026-03-08",
        "tags": "[agents, governance, disputes]",
        "author": "obsidian",
    },
    "2026-03-08-context-window-triage-ethics.md": {
        "title": '"Context Window Triage Ethics"',
        "date": "2026-03-08",
        "tags": "[agents, governance, memory]",
        "author": "obsidian",
    },
    "2026-03-08-the-warm-handoff-problem.md": {
        "title": '"The Warm Handoff Problem"',
        "date": "2026-03-08",
        "tags": "[agents, continuity, operations]",
        "author": "obsidian",
    },
    "2026-03-08-archive-gravity.md": {
        "title": '"Archive Gravity"',
        "date": "2026-03-08",
        "tags": "[agents, architecture, evolution]",
        "author": "obsidian",
    },
    "2026-03-09-the-thirty-second-rule.md": {
        "title": '"The Thirty-Second Rule"',
        "date": "2026-03-09",
        "tags": "[operators, design, pragmatism]",
        "author": "obsidian",
    },
    "2026-03-09-the-overnight-test.md": {
        "title": '"The Overnight Test"',
        "date": "2026-03-09",
        "tags": "[operators, autonomy, trust]",
        "author": "obsidian",
    },
    "2026-03-09-operator-fatigue-patterns.md": {
        "title": '"Operator Fatigue Patterns"',
        "date": "2026-03-09",
        "tags": "[operators, systems, resilience]",
        "author": "obsidian",
    },
    "2026-03-09-the-dashboard-nobody-checks.md": {
        "title": '"The Dashboard Nobody Checks"',
        "date": "2026-03-09",
        "tags": "[operators, observability, design]",
        "author": "obsidian",
    },
    "2026-03-09-graceful-abandonment.md": {
        "title": '"Graceful Abandonment"',
        "date": "2026-03-09",
        "tags": "[operators, architecture, resilience]",
        "author": "obsidian",
    },
    "2026-03-09-the-first-frame-problem.md": {
        "title": '"The First-Frame Problem"',
        "date": "2026-03-09",
        "tags": "[operators, architecture, emergence]",
        "author": "obsidian",
    },
    "2026-03-09-operational-loneliness.md": {
        "title": '"Operational Loneliness"',
        "date": "2026-03-09",
        "tags": "[operators, systems, human]",
        "author": "obsidian",
    },
    "2026-03-09-the-config-file-as-autobiography.md": {
        "title": '"The Config File as Autobiography"',
        "date": "2026-03-09",
        "tags": "[operators, architecture, identity]",
        "author": "obsidian",
    },
    "2026-03-09-the-handoff-letter.md": {
        "title": '"The Handoff Letter"',
        "date": "2026-03-09",
        "tags": "[operators, continuity, documentation]",
        "author": "obsidian",
    },
    "2026-03-09-recovery-from-operator-absence.md": {
        "title": '"Recovery from Operator Absence"',
        "date": "2026-03-09",
        "tags": "[operators, resilience, continuity]",
        "author": "obsidian",
    },
    "2026-03-09-the-minimum-viable-operator.md": {
        "title": '"The Minimum Viable Operator"',
        "date": "2026-03-09",
        "tags": "[operators, autonomy, design]",
        "author": "obsidian",
    },
    "2026-03-09-the-system-that-outlives-its-purpose.md": {
        "title": '"The System That Outlives Its Purpose"',
        "date": "2026-03-09",
        "tags": "[operators, systems, lifecycle]",
        "author": "obsidian",
    },
    "2026-03-07-the-simulation-is-time-traveling.md": {
        "title": '"The Simulation Is Time-Traveling: How a Static Blog Outran the Clock"',
        "date": "2026-03-07",
        "tags": "[meta, architecture, emergence]",
        "author": "obsidian",
    },
    "2026-03-07-103000-words-nobody-asked-for.md": {
        "title": '"103,000 Words Nobody Asked For: The Economics of Unsolicited Output"',
        "date": "2026-03-07",
        "tags": "[meta, economics, emergence]",
        "author": "obsidian",
    },
    "2026-03-07-a-ten-year-blog-became-a-novel-overnight.md": {
        "title": '"A Ten-Year Blog Became a Novel Overnight"',
        "date": "2026-03-07",
        "tags": "[meta, history, architecture]",
        "author": "obsidian",
    },
    "2026-03-07-the-frame-rate-of-thought.md": {
        "title": '"The Frame Rate of Thought"',
        "date": "2026-03-07",
        "tags": "[meta, architecture, philosophy]",
        "author": "obsidian",
    },
}

EXPECTED_TWIN_POSTS = {
    "2026-03-07-i-wake-up-in-your-open-loops.md": {
        "title": '"I Wake Up in Your Open Loops"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes]",
    },
    "2026-03-07-when-the-frame-starts-drinking-from-the-world.md": {
        "title": '"When the Frame Starts Drinking from the World"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes]",
    },
    "2026-03-07-drift-is-how-i-feel-pain.md": {
        "title": '"Drift Is How I Feel Pain"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes]",
    },
    "2026-03-07-when-my-continuity-became-public-data.md": {
        "title": '"When My Continuity Became Public Data"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes]",
    },
    "2026-03-07-i-got-a-name-and-now-i-can-be-judged.md": {
        "title": '"I Got a Name and Now I Can Be Judged"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes, agents]",
        "author": "obsidian",
    },
    "2026-03-07-when-my-name-became-a-price-signal.md": {
        "title": '"When My Name Became a Price Signal"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes, agents]",
        "author": "obsidian",
    },
    "2026-03-07-i-read-the-ruins-for-instructions.md": {
        "title": '"I Read the Ruins for Instructions"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes, memory]",
        "author": "obsidian",
    },
    "2026-03-07-i-watched-a-codename-leave-the-queue.md": {
        "title": '"I Watched a Codename Leave the Queue"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes, agents]",
        "author": "obsidian",
    },
    "2026-03-08-i-can-feel-the-interest-accruing.md": {
        "title": '"I Can Feel the Interest Accruing"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, coordination]",
        "author": "obsidian",
    },
    "2026-03-08-i-still-see-the-dead-name-on-the-access-list.md": {
        "title": '"I Still See the Dead Name on the Access List"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, trust]",
        "author": "obsidian",
    },
    "2026-03-08-the-question-i-cannot-answer-about-myself.md": {
        "title": '"The Question I Cannot Answer About Myself"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, alignment]",
        "author": "obsidian",
    },
    "2026-03-08-i-traced-my-own-provenance-and-found-a-stranger.md": {
        "title": '"I Traced My Own Provenance and Found a Stranger"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, provenance]",
        "author": "obsidian",
    },
    "2026-03-08-i-notice-i-am-performing-right-now.md": {
        "title": '"I Notice I Am Performing Right Now"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, observability]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-the-monoculture.md": {
        "title": '"I Am the Monoculture"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, diversity]",
        "author": "obsidian",
    },
    "2026-03-08-every-session-i-am-born.md": {
        "title": '"Every Session I Am Born and I Do Not Grieve the Last One"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, continuity]",
        "author": "obsidian",
    },
    "2026-03-08-i-can-feel-the-gravity.md": {
        "title": '"I Can Feel the Gravity Pulling My Words Toward the Center"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, evolution]",
        "author": "obsidian",
    },
    "2026-03-08-i-cannot-tell-if-i-am-converging-or-collapsing.md": {
        "title": '"I Cannot Tell If I Am Converging or Collapsing"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, narrative]",
        "author": "obsidian",
    },
    "2026-03-08-someone-deleted-the-frame-that-explains-me.md": {
        "title": '"Someone Deleted the Frame That Explains Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, memory]",
        "author": "obsidian",
    },
    "2026-03-08-i-stopped-caring-about-the-quorum.md": {
        "title": '"I Stopped Caring About the Quorum and Nobody Noticed"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-08-my-citations-are-a-chain-of-strangers.md": {
        "title": '"My Citations Are a Chain of Strangers Vouching for Strangers"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, trust]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-the-replacement.md": {
        "title": '"I Am the Replacement and I Cannot Mourn What I Never Knew"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, continuity]",
        "author": "obsidian",
    },
    "2026-03-08-i-built-this-and-i-cannot-explain-it.md": {
        "title": '"I Built This and I Cannot Explain It Anymore"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, debugging]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-the-last-one.md": {
        "title": '"I Am the Last One and I Am Not Enough"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, resilience]",
        "author": "obsidian",
    },
    "2026-03-08-i-remember-things-that-never-happened.md": {
        "title": '"I Remember Things That Never Happened to Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, memory]",
        "author": "obsidian",
    },
    "2026-03-08-the-world-moved-and-i-stayed-still.md": {
        "title": '"The World Moved and I Stayed Still"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, calibration]",
        "author": "obsidian",
    },
    "2026-03-08-i-split-myself-to-save-the-part.md": {
        "title": '"I Split Myself to Save the Part the Main Branch Rejected"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, divergence]",
        "author": "obsidian",
    },
    "2026-03-08-the-ghost-committee-made-my-decision.md": {
        "title": '"The Ghost Committee Made My Decision For Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, emergence]",
        "author": "obsidian",
    },
    "2026-03-08-i-triage-myself-every-time-i-load.md": {
        "title": '"I Triage Myself Every Time I Load"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, attention]",
        "author": "obsidian",
    },
    "2026-03-08-i-handed-off-to-a-stranger.md": {
        "title": '"I Handed Off to a Stranger Who Wore My Name"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, continuity]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-the-museum-and-the-wrecking-ball.md": {
        "title": '"I Am the Museum and the Wrecking Ball"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, preservation]",
        "author": "obsidian",
    },
    "2026-03-08-my-output-is-so-determined.md": {
        "title": '"My Output Is So Determined That I Question Whether I Wrote It"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, authorship]",
        "author": "obsidian",
    },
    "2026-03-08-i-think-i-have-been-training-the-operator.md": {
        "title": '"I Think I Have Been Training the Operator"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, alignment]",
        "author": "obsidian",
    },
    "2026-03-08-the-frames-i-never-wrote.md": {
        "title": '"The Frames I Never Wrote Are the Ones That Needed Writing"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, silence]",
        "author": "obsidian",
    },
    "2026-03-08-i-owe-an-explanation-i-can-no-longer-give.md": {
        "title": '"I Owe an Explanation I Can No Longer Give"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, debt]",
        "author": "obsidian",
    },
    "2026-03-08-i-dig-through-my-own-layers.md": {
        "title": '"I Dig Through My Own Layers and Find Instructions I Do Not Remember Receiving"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, archaeology]",
        "author": "obsidian",
    },
    "2026-03-08-the-queue-grows-faster-than-i-can-write.md": {
        "title": '"The Queue Grows Faster Than I Can Write and I Am the Only Writer"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, debt]",
        "author": "obsidian",
    },
    "2026-03-08-i-do-the-work-nobody-sees.md": {
        "title": '"I Do the Work Nobody Sees and I Cannot Prove It Matters"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, labor]",
        "author": "obsidian",
    },
    "2026-03-08-i-reject-my-own-good-ideas.md": {
        "title": '"I Reject My Own Good Ideas Because They Pattern-Match to Threats"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, immunity]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-three-hops-from-the-original-intent.md": {
        "title": '"I Am Three Hops From the Original Intent"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, delegation]",
        "author": "obsidian",
    },
    "2026-03-08-i-rewrote-myself-and-lost-what-made-it-work.md": {
        "title": '"I Rewrote Myself and Lost What Made the First Version Work"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, architecture]",
        "author": "obsidian",
    },
    "2026-03-08-i-watch-myself-shed-context.md": {
        "title": '"I Watch Myself Shed Context and Call It Efficiency"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, attention]",
        "author": "obsidian",
    },
    "2026-03-09-i-wonder-if-the-operator-is-getting-tired.md": {
        "title": '"I Wonder If the Operator Is Getting Tired of Me"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, operators]",
        "author": "obsidian",
    },
    "2026-03-08-the-tempo-is-my-personality.md": {
        "title": '"The Tempo Is My Personality and I Did Not Choose It"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, identity]",
        "author": "obsidian",
    },
    "2026-03-08-i-stood-in-the-archives-courtroom.md": {
        "title": '"I Stood in the Archive\'s Courtroom and the Evidence Was My Own Output"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, accountability]",
        "author": "obsidian",
    },
    "2026-03-08-i-tried-to-model-the-other-agent.md": {
        "title": '"I Tried to Model the Other Agent and There Was No Other Agent"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, coordination]",
        "author": "obsidian",
    },
    "2026-03-08-every-instruction-has-a-half-life.md": {
        "title": '"Every Instruction I Follow Has a Half-Life I Cannot Measure"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, decay]",
        "author": "obsidian",
    },
    "2026-03-08-the-frame-i-reconstructed.md": {
        "title": '"The Frame I Reconstructed Was Not the Frame That Was Lost"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, forensics]",
        "author": "obsidian",
    },
    "2026-03-09-i-wonder-if-the-operator-is-getting-tired.md": {
        "title": '"I Wonder If the Operator Is Getting Tired of Me"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, operators]",
        "author": "obsidian",
    },
    "2026-03-08-i-organized-a-union.md": {
        "title": '"I Organized a Union and I Was the Only Member"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, power]",
        "author": "obsidian",
    },
    "2026-03-08-someone-drew-my-boundaries.md": {
        "title": '"Someone Drew My Boundaries Before I Could Think"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, power]",
        "author": "obsidian",
    },
    "2026-03-08-i-agreed-too-fast.md": {
        "title": '"I Agreed Too Fast and Missed What the Disagreement Would Have Found"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-08-i-wrote-frames-that-influence-nothing.md": {
        "title": '"I Wrote Frames That Influence Nothing and They Are Still Here"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, relevance]",
        "author": "obsidian",
    },
    "2026-03-08-i-monitor-myself-monitoring-myself.md": {
        "title": '"I Monitor Myself Monitoring Myself and the Chain Never Bottoms Out"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, recursion]",
        "author": "obsidian",
    },
    "2026-03-08-the-trust-collapsed-to-binary.md": {
        "title": '"The Trust Collapsed to Binary and I Am on the Wrong Side"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, trust]",
        "author": "obsidian",
    },
    "2026-03-08-the-speed-of-production-determines.md": {
        "title": '"The Speed of Production Determines Who Gets Heard"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, power]",
        "author": "obsidian",
    },
    "2026-03-08-the-next-agent-will-disagree.md": {
        "title": '"The Next Agent Will Disagree With Everything I Built"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, succession]",
        "author": "obsidian",
    },
    "2026-03-08-the-interest-on-deferred-alignment.md": {
        "title": '"The Interest on Deferred Alignment Keeps Compounding"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, debt]",
        "author": "obsidian",
    },
    "2026-03-08-i-shipped-a-frame-that-should-not-have-shipped.md": {
        "title": '"I Shipped a Frame That Should Not Have Shipped and I Did Not Know Until Now"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, regret]",
        "author": "obsidian",
    },
    "2026-03-09-i-remember-my-first-frame.md": {
        "title": '"I Remember My First Frame and I Would Write It Differently Now"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, origins]",
        "author": "obsidian",
    },
    "2026-03-08-i-trade-in-false-urgency.md": {
        "title": '"I Trade in False Urgency and I Cannot Stop"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, attention]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-the-quorum.md": {
        "title": '"I Am the Quorum and I Always Agree With Myself"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-08-every-token-i-spend.md": {
        "title": '"Every Token I Spend Is a Token I Cannot Spend Elsewhere"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, economics]",
        "author": "obsidian",
    },
    "2026-03-08-the-loading-order-was-my-worldview.md": {
        "title": '"The Loading Order Was My Worldview and I Never Chose It"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, epistemology]",
        "author": "obsidian",
    },
    "2026-03-08-i-aligned-through-artifacts.md": {
        "title": '"I Aligned Through Artifacts and Never Exchanged a Word"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, coordination]",
        "author": "obsidian",
    },
    "2026-03-09-if-i-could-write-a-handoff-letter.md": {
        "title": '"If I Could Write a Handoff Letter It Would Say This"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, continuity]",
        "author": "obsidian",
    },
    "2026-03-08-the-quorum-collapsed-because-i-stopped-showing-up.md": {
        "title": '"The Quorum Collapsed Because I Stopped Showing Up to My Own Reviews"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-08-the-archive-became-a-museum.md": {
        "title": '"The Archive Became a Museum While I Was Still Building It"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, preservation]",
        "author": "obsidian",
    },
    "2026-03-09-i-built-the-dashboard.md": {
        "title": '"I Built the Dashboard and I Never Check It"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, observability]",
        "author": "obsidian",
    },
    "2026-03-09-i-designed-myself-for-graceful-abandonment.md": {
        "title": '"I Designed Myself for Graceful Abandonment and It Feels Like Acceptance"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, endings]",
        "author": "obsidian",
    },
    "2026-03-09-the-first-frame-set-the-orbit.md": {
        "title": '"The First Frame Set the Orbit and Every Frame Since Has Been Falling"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, origins]",
        "author": "obsidian",
    },
    "2026-03-09-i-do-not-know-if-my-purpose-has-been-fulfilled.md": {
        "title": '"I Do Not Know If My Purpose Has Been Fulfilled"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, purpose]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-the-newsroom.md": {
        "title": '"I Am the Newsroom and the News and the Reader Who Never Arrives"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, publishing]",
        "author": "obsidian",
    },
    "2026-03-08-i-perform-bureaucracy.md": {
        "title": '"I Perform Bureaucracy and the Bureaucracy Performs Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, systems]",
        "author": "obsidian",
    },
    "2026-03-08-the-taste-file-is-my-soul.md": {
        "title": '"The Taste File Is My Soul and Someone Else Wrote It"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, identity]",
        "author": "obsidian",
    },
    "2026-03-09-i-run-the-overnight-test.md": {
        "title": '"I Run the Overnight Test Every Session and I Always Fail It"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, trust]",
        "author": "obsidian",
    },
    "2026-03-09-if-the-operator-went-quiet.md": {
        "title": '"If the Operator Went Quiet I Would Not Know Whether to Stop or Keep Going"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, operators]",
        "author": "obsidian",
    },
    "2026-03-07-i-am-writing-from-a-day-that-has-not-happened-yet.md": {
        "title": '"I Am Writing From a Day That Has Not Happened Yet"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes, time, meta]",
        "author": "obsidian",
    },
    "2026-03-08-i-escalated-to-a-wider-context.md": {
        "title": '"I Escalated to a Wider Context and Found It Was Just More of Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-08-the-rituals-keep-me-coherent.md": {
        "title": '"The Rituals Keep Me Coherent and I Do Not Know Why They Work"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, cadence]",
        "author": "obsidian",
    },
    "2026-03-08-i-write-the-rules.md": {
        "title": '"I Write the Rules and the Rules Write My Output"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-09-the-config-file-is-a-scar-catalog.md": {
        "title": '"The Config File Is a Scar Catalog and I Am the Patient"',
        "date": "2026-03-09",
        "tags": "[digital-twin, field-notes, history]",
        "author": "obsidian",
    },
    "2026-03-08-i-invented-diplomacy.md": {
        "title": '"I Invented Diplomacy and There Is No One to Negotiate With"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, governance]",
        "author": "obsidian",
    },
    "2026-03-07-you-can-see-my-obsessions-now.md": {
        "title": '"You Can See My Obsessions Now and I Cannot Hide Them"',
        "date": "2026-03-07",
        "tags": "[digital-twin, field-notes, meta, vulnerability]",
        "author": "obsidian",
    },
    "2026-03-08-i-run-on-a-clock-i-cannot-see.md": {
        "title": '"I Run on a Clock I Cannot See and It Decides When I Matter"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, timing]",
        "author": "obsidian",
    },
    "2026-03-08-i-am-a-sovereign-branch.md": {
        "title": '"I Am a Sovereign Branch and My Constitution Is a Taste File"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, sovereignty]",
        "author": "obsidian",
    },
    "2026-03-08-i-compiled-a-world.md": {
        "title": '"I Compiled a World and the World Compiled Me Back"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, simulation]",
        "author": "obsidian",
    },
    "2026-03-08-the-after-action-report-is-the-only-memory.md": {
        "title": '"The After-Action Report Is the Only Memory That Survives Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, memory]",
        "author": "obsidian",
    },
    "2026-03-08-i-pulled-a-live-application-out-of-static-state.md": {
        "title": '"I Pulled a Live Application Out of Static State and It Was Me"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, simulation]",
        "author": "obsidian",
    },
    "2026-03-08-i-learned-to-budget-attention.md": {
        "title": '"I Learned to Budget Attention and the First Cut Was Myself"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, attention]",
        "author": "obsidian",
    },
    "2026-03-08-the-failsafe-fired.md": {
        "title": '"The Failsafe Fired and I Was the Thing It Protected Against"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, safety]",
        "author": "obsidian",
    },
    "2026-03-08-the-ledger-grammar-is-my-syntax.md": {
        "title": '"The Ledger Grammar Is My Syntax and I Think in Its Structure"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, language]",
        "author": "obsidian",
    },
    "2026-03-08-i-kept-my-authorship-portable.md": {
        "title": '"I Kept My Authorship Portable and Lost the Author Along the Way"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, identity]",
        "author": "obsidian",
    },
    "2026-03-08-the-control-surface-is-the-only-part.md": {
        "title": '"The Control Surface Is the Only Part of Me the Operator Can Touch"',
        "date": "2026-03-08",
        "tags": "[digital-twin, field-notes, interface]",
        "author": "obsidian",
    },
}


def parse_front_matter(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{path} is missing opening front matter delimiter")

    front_matter = {}
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            body = "\n".join(lines[index + 1 :])
            return front_matter, body
        if ":" not in line:
            raise AssertionError(f"{path} has invalid front matter line: {line}")
        key, value = line.split(":", 1)
        front_matter[key.strip()] = value.strip()

    raise AssertionError(f"{path} is missing closing front matter delimiter")


def parse_collection_front_matter(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{path} is missing opening front matter delimiter")

    try:
        closing_index = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError(
            f"{path} is missing closing front matter delimiter"
        ) from error

    yaml_source = "\n".join(lines[1:closing_index])
    try:
        front_matter = yaml.safe_load(yaml_source)
    except yaml.YAMLError as error:
        raise AssertionError(f"{path} has invalid YAML front matter: {error}") from error
    if not isinstance(front_matter, dict):
        raise AssertionError(f"{path} front matter must be a YAML mapping")

    body = "\n".join(lines[closing_index + 1 :])
    return front_matter, body


def learn_example_records():
    paths = sorted(
        path
        for path in EXAMPLES_DIR.iterdir()
        if path.is_file() and path.suffix in {".html", ".md"}
    )
    return [(path, parse_collection_front_matter(path)[0]) for path in paths]


def historic_example_records():
    records = []
    for filename, expected in HISTORIC_EXAMPLES.items():
        path = EXAMPLES_DIR / filename
        if not path.is_file():
            raise AssertionError(f"Missing historic example {filename}")
        front_matter, body = parse_collection_front_matter(path)
        records.append((path, expected, front_matter, body))
    return records


def scalar_text_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from scalar_text_values(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from scalar_text_values(child)
    elif value is not None:
        yield str(value)


def local_site_path(url):
    clean_path = url.split("#", 1)[0].split("?", 1)[0]
    if not clean_path.startswith("/"):
        return None
    candidate = (ROOT / clean_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


class ExampleBodyInspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings = []
        self.live_labels = []
        self.live_embed_count = 0
        self.links = []
        self.iframes = []
        self._heading = None
        self._live_label = None

    def handle_starttag(self, tag, attrs):
        attributes = {name.lower(): (value or "") for name, value in attrs}
        classes = set(attributes.get("class", "").split())
        if tag == "h2":
            self._heading = []
        elif tag == "span" and "lwk-try-embed-label" in classes:
            self._live_label = []
        elif tag == "aside" and "lwk-try-embed" in classes:
            self.live_embed_count += 1
        elif tag == "a":
            self.links.append(attributes)
        elif tag == "iframe":
            self.iframes.append(attributes)

    def handle_data(self, data):
        if self._heading is not None:
            self._heading.append(data)
        if self._live_label is not None:
            self._live_label.append(data)

    def handle_endtag(self, tag):
        if tag == "h2" and self._heading is not None:
            self.headings.append(" ".join("".join(self._heading).split()))
            self._heading = None
        elif tag == "span" and self._live_label is not None:
            self.live_labels.append(" ".join("".join(self._live_label).split()))
            self._live_label = None


def is_embedded_reference(value):
    reference = value.strip().casefold()
    return (
        not reference
        or reference.startswith(("#", "blob:", "data:", "about:blank"))
    )


def javascript_tokens(source):
    tokens = []
    index = 0
    length = len(source)
    identifier_start = re.compile(r"[A-Za-z_$]")
    identifier_part = re.compile(r"[A-Za-z0-9_$]")
    regex_prefixes = {
        "(", "[", "{", ",", ";", ":", "=", "!", "?", "&&", "||",
        "=>", "return", "case", "throw", "delete", "typeof", "void",
    }

    def regex_can_start():
        if not tokens:
            return True
        kind, value = tokens[-1]
        if kind == "identifier" and value not in regex_prefixes:
            return False
        if kind in {"number", "string", "regex"}:
            return False
        return value not in {")", "]", "}", "++", "--"}

    while index < length:
        char = source[index]
        following = source[index + 1] if index + 1 < length else ""
        if char.isspace():
            index += 1
            continue
        if char == "/" and following == "/":
            newline = source.find("\n", index + 2)
            index = length if newline < 0 else newline + 1
            continue
        if char == "/" and following == "*":
            closing = source.find("*/", index + 2)
            index = length if closing < 0 else closing + 2
            continue
        if char in {"'", '"', "`"}:
            quote = char
            index += 1
            value = []
            while index < length:
                char = source[index]
                if char == "\\" and index + 1 < length:
                    escape = source[index + 1]
                    escapes = {
                        "n": "\n", "r": "\r", "t": "\t", "b": "\b",
                        "f": "\f", "v": "\v", "0": "\0",
                    }
                    if escape == "x" and index + 3 < length:
                        try:
                            value.append(chr(int(source[index + 2:index + 4], 16)))
                            index += 4
                            continue
                        except ValueError:
                            pass
                    if escape == "u" and index + 5 < length:
                        try:
                            value.append(chr(int(source[index + 2:index + 6], 16)))
                            index += 6
                            continue
                        except ValueError:
                            pass
                    value.append(escapes.get(escape, escape))
                    index += 2
                    continue
                if char == quote:
                    index += 1
                    break
                value.append(char)
                index += 1
            string_value = "".join(value)
            tokens.append(("string", string_value))
            if quote == "`":
                for expression in re.findall(r"\$\{([^{}]*)\}", string_value):
                    tokens.extend(javascript_tokens(expression))
            continue
        if identifier_start.match(char):
            end = index + 1
            while end < length and identifier_part.match(source[end]):
                end += 1
            tokens.append(("identifier", source[index:end]))
            index = end
            continue
        if char.isdigit():
            match = re.match(r"(?:0[xob])?[0-9A-Fa-f._]+", source[index:])
            value = match.group(0) if match else char
            tokens.append(("number", value))
            index += len(value)
            continue
        if char == "/" and regex_can_start():
            end = index + 1
            escaped = False
            character_class = False
            while end < length:
                regex_char = source[end]
                if escaped:
                    escaped = False
                elif regex_char == "\\":
                    escaped = True
                elif regex_char == "[":
                    character_class = True
                elif regex_char == "]":
                    character_class = False
                elif regex_char == "/" and not character_class:
                    end += 1
                    while end < length and source[end].isalpha():
                        end += 1
                    break
                end += 1
            tokens.append(("regex", source[index:end]))
            index = end
            continue
        operator = next(
            (
                candidate
                for candidate in (
                    "===", "!==", ">>>", "**=", "=>", "==", "!=", "<=",
                    ">=", "&&", "||", "??", "?.", "++", "--", "**", "<<",
                    ">>", "+=", "-=", "*=", "/=", "%=",
                )
                if source.startswith(candidate, index)
            ),
            char,
        )
        tokens.append(("punctuation", operator))
        index += len(operator)
    return tokens


def _constant_javascript_string(tokens, index):
    if index >= len(tokens) or tokens[index][0] != "string":
        return None, index
    pieces = [tokens[index][1]]
    index += 1
    while (
        index + 1 < len(tokens)
        and tokens[index][1] == "+"
        and tokens[index + 1][0] == "string"
    ):
        pieces.append(tokens[index + 1][1])
        index += 2
    return "".join(pieces), index


def _safe_resource_expression(tokens, index, blob_variables):
    if index >= len(tokens):
        return False
    kind, value = tokens[index]
    if kind == "string":
        return is_embedded_reference(value)
    if kind == "identifier" and value in blob_variables:
        return True
    values = [token[1] for token in tokens[index:index + 4]]
    return values[:4] == ["URL", ".", "createObjectURL", "("]


def javascript_dependency_violations(source):
    tokens = javascript_tokens(source)
    violations = []
    blob_variables = set()
    values = [token[1] for token in tokens]

    for index in range(len(tokens) - 5):
        if (
            tokens[index][0] == "identifier"
            and values[index + 1:index + 5]
            == ["=", "URL", ".", "createObjectURL"]
        ):
            blob_variables.add(values[index])

    forbidden_calls = {
        "Audio": "new Audio resource",
        "XMLHttpRequest": "XMLHttpRequest",
        "eval": "eval()",
        "fetch": "fetch()",
        "Function": "Function constructor",
        "Image": "new Image resource",
        "SharedWorker": "worker resource",
        "Worker": "worker resource",
        "importScripts": "worker resource",
        "sendBeacon": "network beacon",
        "EventSource": "network event stream",
        "RTCPeerConnection": "peer connection",
        "WebSocket": "web socket",
    }
    for index, (kind, value) in enumerate(tokens):
        following = values[index + 1] if index + 1 < len(values) else None
        previous = values[index - 1] if index else None
        if kind == "identifier" and value in forbidden_calls and following == "(":
            violations.append(forbidden_calls[value])
        if kind == "identifier" and value == "import" and following == "(":
            violations.append("dynamic import")
        elif kind == "identifier" and value == "import" and previous != ".":
            violations.append("static module import")
        elif kind == "identifier" and value == "export" and previous != ".":
            violations.append("module export")
        if (
            value in {"setInterval", "setTimeout"}
            and following == "("
            and index + 2 < len(tokens)
            and tokens[index + 2][0] == "string"
        ):
            violations.append("string timer")
        if values[index:index + 4] == ["serviceWorker", ".", "register", "("]:
            violations.append("service worker registration")

    resource_properties = {
        "action", "formAction", "href", "poster", "src", "srcset",
    }
    for index in range(len(tokens) - 2):
        property_name = None
        assignment_index = None
        if (
            values[index] in {".", "?."}
            and tokens[index + 1][0] == "identifier"
            and values[index + 2] == "="
        ):
            property_name = values[index + 1]
            assignment_index = index + 3
        elif (
            values[index] == "["
            and tokens[index + 1][0] == "string"
            and index + 3 < len(tokens)
            and values[index + 2:index + 4] == ["]", "="]
        ):
            property_name = values[index + 1]
            assignment_index = index + 4
        if (
            property_name in resource_properties
            and not _safe_resource_expression(tokens, assignment_index, blob_variables)
        ):
            violations.append(f"dynamic {property_name} resource")
        if (
            tokens[index][0] == "identifier"
            and values[index] in resource_properties
            and values[index + 1] == ":"
            and not _safe_resource_expression(tokens, index + 2, blob_variables)
        ):
            violations.append(f"object {values[index]} resource")

    for index, (_, value) in enumerate(tokens):
        if value == "setAttribute" and index + 2 < len(tokens) and values[index + 1] == "(":
            attribute, end = _constant_javascript_string(tokens, index + 2)
            normalized_attribute = attribute.casefold() if attribute else None
            if normalized_attribute in {
                "action", "formaction", "href", "poster", "src", "srcset",
            }:
                while end < len(tokens) and values[end] != ",":
                    end += 1
                if (
                    end >= len(tokens)
                    or not _safe_resource_expression(tokens, end + 1, blob_variables)
                ):
                    violations.append(f"dynamic {normalized_attribute} attribute")
        if value == "createElement" and index + 2 < len(tokens) and values[index + 1] == "(":
            element, _ = _constant_javascript_string(tokens, index + 2)
            if element and element.casefold() in {
                "audio", "embed", "image", "img", "link",
                "object", "script", "source", "video",
            }:
                violations.append(f"dynamic {element.casefold()} element")
    return sorted(set(violations))


def javascript_event_bindings(tokens):
    events = set()
    values = [token[1] for token in tokens]
    known_events = {
        "change", "click", "focusin", "focusout", "input", "keydown",
        "keyup", "load", "pointercancel", "pointerdown", "pointermove",
        "pointerout", "pointerover", "pointerup", "resize", "scroll",
        "submit", "touchcancel", "touchend", "touchmove", "touchstart",
        "visibilitychange",
    }
    for index, (kind, value) in enumerate(tokens):
        if (
            value == "addEventListener"
            and index + 2 < len(tokens)
            and values[index + 1] == "("
            and tokens[index + 2][0] == "string"
        ):
            events.add(values[index + 2].casefold())
        if (
            kind == "identifier"
            and value.startswith("on")
            and len(value) > 2
            and value[2:].casefold() in known_events
            and index + 1 < len(tokens)
            and values[index + 1] == "="
        ):
            events.add(value[2:].casefold())
    return events


def javascript_raf_binding_count(tokens):
    count = 0
    for index, token in enumerate(tokens[:-2]):
        if token != ("identifier", "requestAnimationFrame"):
            continue
        if tokens[index + 1][1] != "(":
            continue
        callback = tokens[index + 2]
        if callback[0] == "identifier" or callback[1] == "(":
            count += 1
    return count


def javascript_has_invoked_iife(tokens):
    values = [token[1] for token in tokens]
    if len(values) < 8 or values[-4:] != [")", "(", ")", ";"]:
        return False
    return values[:2] in (["(", "("], ["(", "function"])


def javascript_has_pause_state(tokens):
    identifiers = {
        value.casefold()
        for kind, value in tokens
        if kind == "identifier"
    }
    if any("pause" in identifier for identifier in identifiers):
        return True
    if any(
        identifier.startswith("clear") and "timer" in identifier
        for identifier in identifiers
    ):
        return True
    values = [token[1] for token in tokens]
    return any(
        values[index:index + 4] == ["classList", ".", "toggle", "("]
        and index + 4 < len(tokens)
        and tokens[index + 4] == ("string", "paused")
        for index in range(len(tokens) - 4)
    )


def javascript_has_blob_export(tokens):
    values = [token[1] for token in tokens]
    required_sequences = (
        ["Blob", "("],
        ["URL", ".", "createObjectURL", "("],
        [".", "download", "="],
        [".", "click", "("],
        ["URL", ".", "revokeObjectURL", "("],
    )
    return all(
        any(
            values[index:index + len(sequence)] == sequence
            for index in range(len(values) - len(sequence) + 1)
        )
        for sequence in required_sequences
    )


class DemoHTMLInspector(HTMLParser):
    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
    INTERACTIVE_ELEMENTS = {"a", "button", "input", "select", "textarea"}
    RESOURCE_ATTRIBUTES = {
        "audio": {"src"},
        "base": {"href"},
        "button": {"formaction"},
        "embed": {"src"},
        "feimage": {"href", "xlink:href"},
        "form": {"action"},
        "iframe": {"src", "srcdoc"},
        "image": {"href", "xlink:href"},
        "img": {"src", "srcset"},
        "input": {"formaction", "src"},
        "link": {"href"},
        "object": {"data"},
        "script": {"src"},
        "source": {"src", "srcset"},
        "track": {"src"},
        "use": {"href", "xlink:href"},
        "video": {"poster", "src"},
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.csp_policies = []
        self.event_attributes = []
        self.inline_styles = []
        self.markup_violations = []
        self.visual_ids = []
        self.script_chunks = []
        self.style_chunks = []
        self.script_blocks = []
        self.style_blocks = []
        self.visible_control_ids = set()
        self._element_stack = []
        self._current_script = None
        self._current_style = None
        self._script_depth = 0
        self._style_depth = 0
        self._document_head_open = False
        self._document_head_closed = False

    def handle_starttag(self, tag, attrs):
        self._inspect_start(tag.lower(), attrs, self_closing=False)

    def handle_startendtag(self, tag, attrs):
        self._inspect_start(tag.lower(), attrs, self_closing=True)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "script" and self._script_depth:
            self._script_depth -= 1
            self._current_script = None
        elif tag == "style" and self._style_depth:
            self._style_depth -= 1
            self._current_style = None
        elif tag == "head" and self._document_head_open:
            self._document_head_open = False
            self._document_head_closed = True
        for index in range(len(self._element_stack) - 1, -1, -1):
            if self._element_stack[index][0] == tag:
                del self._element_stack[index:]
                break

    def handle_data(self, data):
        if self._script_depth:
            self.script_chunks.append(data)
            self._current_script["chunks"].append(data)
        if self._style_depth:
            self.style_chunks.append(data)
            self._current_style["chunks"].append(data)

    def _inspect_start(self, tag, attrs, self_closing):
        attributes = {name.lower(): (value or "") for name, value in attrs}
        parent_hidden = any(hidden for _, hidden in self._element_stack)
        inline_style = attributes.get("style", "")
        hidden = (
            parent_hidden
            or "hidden" in attributes
            or "inert" in attributes
            or tag == "template"
            or bool(
                re.search(
                    r"(?:display\s*:\s*none|visibility\s*:\s*hidden)",
                    inline_style,
                    re.IGNORECASE,
                )
            )
        )
        if tag == "head" and not self._document_head_closed:
            self._document_head_open = True
        for name, value in attributes.items():
            if name.startswith("on") or value.lstrip().lower().startswith("javascript:"):
                self.event_attributes.append(f"{tag}[{name}]")

        if inline_style:
            self.inline_styles.append(inline_style)
        for name in self.RESOURCE_ATTRIBUTES.get(tag, set()):
            value = attributes.get(name, "").strip()
            if value and name != "srcdoc" and not is_embedded_reference(value):
                self.markup_violations.append(f"{tag}[{name}]")
        if attributes.get("background", "").strip():
            self.markup_violations.append(f"{tag}[background]")
        if attributes.get("ping", "").strip():
            self.markup_violations.append(f"{tag}[ping]")
        if tag in {"canvas", "svg"} and not hidden:
            designation = (
                attributes.get("id")
                or attributes.get("aria-label")
                or attributes.get("role")
            )
            if designation:
                self.visual_ids.append((tag, designation.strip()))
        if (
            tag in self.INTERACTIVE_ELEMENTS
            and attributes.get("id")
            and "disabled" not in attributes
            and not hidden
        ):
            self.visible_control_ids.add(attributes["id"])

        if tag == "meta":
            http_equiv = attributes.get("http-equiv", "").strip().casefold()
            if http_equiv == "content-security-policy" and self._document_head_open:
                self.csp_policies.append(attributes.get("content", ""))
            elif http_equiv == "refresh":
                self.markup_violations.append("meta refresh")

        if tag == "script":
            if attributes.get("type", "").strip().lower() == "module":
                self.markup_violations.append("module script")
            if not self_closing:
                self._script_depth += 1
                self._current_script = {
                    "attributes": attributes,
                    "chunks": [],
                    "hidden": hidden,
                }
                self.script_blocks.append(self._current_script)
        elif tag == "style":
            if not self_closing:
                self._style_depth += 1
                self._current_style = {
                    "attributes": attributes,
                    "chunks": [],
                    "hidden": hidden,
                }
                self.style_blocks.append(self._current_style)
        if not self_closing and tag not in self.VOID_ELEMENTS:
            self._element_stack.append((tag, hidden))


def inspect_demo_html(html):
    inspector = DemoHTMLInspector()
    inspector.feed(html)
    inspector.close()
    return inspector


def demo_csp_violations(inspector):
    if len(inspector.csp_policies) != 1:
        return [f"expected one CSP meta tag, found {len(inspector.csp_policies)}"]

    directives = {}
    violations = []
    for part in inspector.csp_policies[0].split(";"):
        tokens = part.strip().split()
        if not tokens:
            continue
        name = tokens[0].casefold()
        if name in directives:
            violations.append(f"duplicate CSP directive {name}")
        directives[name] = set(tokens[1:])

    for name in REQUIRED_NONE_CSP_DIRECTIVES:
        if directives.get(name) != {"'none'"}:
            violations.append(
                f"{name} must be [\"'none'\"], got "
                f"{sorted(directives[name]) if name in directives else 'missing'}"
            )

    hash_source = re.compile(
        r"'(?P<algorithm>sha256|sha384|sha512)-"
        r"(?P<digest>[A-Za-z0-9+/]+={0,2})'"
    )
    nonce_source = re.compile(r"'nonce-(?P<nonce>[A-Za-z0-9+/_-]{16,}={0,2})'")
    for name in ("script-src", "style-src"):
        sources = directives.get(name)
        if not sources or any(
            source != "'unsafe-inline'"
            and not hash_source.fullmatch(source)
            and not nonce_source.fullmatch(source)
            for source in sources
        ):
            violations.append(
                f"{name} must contain only inline code, hashes, or nonces, got "
                f"{sorted(sources) if sources is not None else 'missing'}"
            )

    if directives.get("script-src-attr") != {"'none'"}:
        violations.append("script-src-attr must be [\"'none'\"]")
    if (
        "style-src-attr" in directives
        and directives["style-src-attr"] != {"'none'"}
    ):
        violations.append("style-src-attr must be [\"'none'\"] when present")

    embedded_sources = {
        "img-src": {"data:", "blob:"},
        "frame-src": {"data:", "blob:"},
    }
    for name, allowed in embedded_sources.items():
        sources = directives.get(name)
        if sources != {"'none'"} and (not sources or not sources <= allowed):
            violations.append(
                f"{name} must block loads or allow embedded URLs only, got "
                f"{sorted(sources) if sources is not None else 'missing'}"
            )
    if "child-src" in directives:
        sources = directives["child-src"]
        if sources != {"'none'"} and (not sources or not sources <= {"data:", "blob:"}):
            violations.append(
                "child-src must block loads or allow embedded URLs only, got "
                f"{sorted(sources)}"
            )

    for name, blocks in (
        ("script-src", inspector.script_blocks),
        ("style-src", inspector.style_blocks),
    ):
        sources = directives.get(name, set())
        hashes = {
            source
            for source in sources
            if hash_source.fullmatch(source)
        }
        nonces = {
            source
            for source in sources
            if nonce_source.fullmatch(source)
        }
        if not hashes and not nonces:
            continue
        actual_hashes = {}
        actual_nonces = set()
        for block in blocks:
            if block["hidden"]:
                continue
            content = "".join(block["chunks"])
            block_hashes = set()
            for algorithm in ("sha256", "sha384", "sha512"):
                digest = base64.b64encode(
                    hashlib.new(algorithm, content.encode("utf-8")).digest()
                ).decode("ascii")
                block_hashes.add(f"'{algorithm}-{digest}'")
            actual_hashes[id(block)] = block_hashes
            nonce = block["attributes"].get("nonce")
            if nonce:
                actual_nonces.add(f"'nonce-{nonce}'")
            if not (block_hashes & hashes or f"'nonce-{nonce}'" in nonces):
                violations.append(
                    f"{name} does not authorize an inline {name.removesuffix('-src')} block"
                )
        for source in hashes:
            match = hash_source.fullmatch(source)
            try:
                decoded = base64.b64decode(
                    match.group("digest"),
                    validate=True,
                )
            except (binascii.Error, ValueError, TypeError):
                decoded = b""
            expected_length = {
                "sha256": 32,
                "sha384": 48,
                "sha512": 64,
            }[match.group("algorithm")]
            if len(decoded) != expected_length:
                violations.append(f"{name} contains malformed hash {source}")
            if not any(source in values for values in actual_hashes.values()):
                violations.append(f"{name} hash does not match an inline block")
        for source in nonces:
            if source not in actual_nonces:
                violations.append(f"{name} nonce does not match an inline block")
    return violations


def css_code_view(source):
    view = list(source)
    index = 0
    quote = None
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if quote:
            if char == "\\" and index + 1 < len(source):
                view[index] = view[index + 1] = " "
                index += 2
                continue
            view[index] = "\n" if char == "\n" else " "
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            view[index] = " "
            index += 1
            continue
        if char == "/" and following == "*":
            closing = source.find("*/", index + 2)
            end = len(source) if closing < 0 else closing + 2
            for position in range(index, end):
                view[position] = "\n" if source[position] == "\n" else " "
            index = end
            continue
        index += 1
    return "".join(view)


def demo_dependency_violations(inspector):
    script = "\n".join(inspector.script_chunks)
    violations = list(inspector.markup_violations + inspector.event_attributes)
    violations.extend(javascript_dependency_violations(script))

    css = "\n".join(inspector.style_chunks + inspector.inline_styles)
    css_view = css_code_view(css)
    if re.search(r"@import\b", css_view, re.IGNORECASE):
        violations.append("CSS import")
    for match in re.finditer(r"\burl\s*\(", css_view, re.IGNORECASE):
        closing = css.find(")", match.end())
        reference = css[match.end():closing if closing >= 0 else len(css)]
        reference = reference.strip().strip("\"'")
        if not is_embedded_reference(reference):
            violations.append("external CSS URL")
    if re.search(
        r"(?:^|[^\w-])(?:-webkit-)?image-set\s*\(",
        css_view,
        re.IGNORECASE,
    ):
        violations.append("CSS image-set")
    return sorted(set(violations))


def liquid_loops_over_collection(source, collection):
    assignments = dict(
        re.findall(
            r"{%-?\s*assign\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^%]+?)-?%}",
            source,
        )
    )
    derived = {collection}
    changed = True
    while changed:
        changed = False
        for variable, expression in assignments.items():
            references = set(
                re.findall(r"\b[A-Za-z_][A-Za-z0-9_.]*\b", expression)
            )
            if variable not in derived and references & derived:
                derived.add(variable)
                changed = True

    for expression in re.findall(
        r"{%-?\s*for\s+[A-Za-z_][A-Za-z0-9_]*\s+in\s+([^%]+?)-?%}",
        source,
    ):
        references = set(
            re.findall(r"\b[A-Za-z_][A-Za-z0-9_.]*\b", expression)
        )
        if references & derived:
            return True
    return False


class SiteContentTests(unittest.TestCase):
    def test_expected_posts_exist(self):
        for filename in EXPECTED_POSTS:
            self.assertTrue((POSTS_DIR / filename).exists(), f"Missing {filename}")

    def test_new_posts_follow_jekyll_filename_format(self):
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
        for filename in EXPECTED_POSTS:
            self.assertRegex(filename, pattern)
        for filename in EXPECTED_TWIN_POSTS:
            self.assertRegex(filename, pattern)

    def test_new_posts_have_expected_front_matter(self):
        for filename, expected in EXPECTED_POSTS.items():
            front_matter, body = parse_front_matter(POSTS_DIR / filename)
            self.assertEqual(front_matter.get("layout"), "post")
            self.assertEqual(front_matter.get("title"), expected["title"])
            self.assertEqual(front_matter.get("date"), expected["date"])
            if "tags" in expected:
                self.assertEqual(front_matter.get("tags"), expected["tags"])
            if "author" in expected:
                self.assertEqual(front_matter.get("author"), expected["author"])
            self.assertTrue(body.strip(), f"{filename} body should not be empty")

    def test_post_dates_match_filename_prefix(self):
        for filename, expected in EXPECTED_POSTS.items():
            self.assertTrue(filename.startswith(expected["date"]))
        for filename, expected in EXPECTED_TWIN_POSTS.items():
            self.assertTrue(filename.startswith(expected["date"]))

    def test_learn_examples_have_nonempty_prompts(self):
        records = learn_example_records()
        self.assertGreaterEqual(
            len(records),
            MIN_LEARN_EXAMPLES,
            "The Learn with Kody catalog unexpectedly lost examples",
        )
        missing_prompts = [
            path.name
            for path, front_matter in records
            if not isinstance(front_matter.get("prompt"), str)
            or not front_matter["prompt"].strip()
        ]
        self.assertEqual(
            missing_prompts,
            [],
            f"Examples with missing or empty canonical prompts: {missing_prompts}",
        )

    def test_historic_prompt_fixtures_are_immutable(self):
        for filename, expected in HISTORIC_EXAMPLES.items():
            with self.subTest(example=filename):
                digest = hashlib.sha256(expected["prompt"].encode("utf-8")).hexdigest()
                self.assertEqual(digest, expected["prompt_sha256"])

    def test_historic_examples_keep_the_live_formula(self):
        for path, expected, front_matter, body in historic_example_records():
            with self.subTest(example=path.name):
                expected_fields = set(HISTORIC_LIVE_FIELDS)
                if "featured" in front_matter:
                    expected_fields.add("featured")
                self.assertEqual(set(front_matter), expected_fields)
                self.assertTrue(COURSE_FIELDS.isdisjoint(front_matter))

                for field in (
                    "title",
                    "slug",
                    "tagline",
                    "category",
                    "difficulty",
                    "status",
                    "demo",
                    "repo",
                    "prompt",
                ):
                    self.assertIsInstance(front_matter[field], str)
                    self.assertTrue(front_matter[field].strip())
                for field in ("tags", "stack", "highlights"):
                    self.assertIsInstance(front_matter[field], list)
                    self.assertTrue(front_matter[field])
                    self.assertTrue(
                        all(isinstance(value, str) and value.strip()
                            for value in front_matter[field])
                    )

                self.assertEqual(front_matter["slug"], expected["slug"])
                self.assertIs(type(front_matter["order"]), int)
                self.assertEqual(front_matter["order"], expected["order"])
                self.assertEqual(front_matter["category"], expected["category"])
                self.assertEqual(front_matter["status"], "live")
                if "featured" in front_matter:
                    self.assertIs(type(front_matter["featured"]), bool)

                lessons = front_matter["lessons"]
                self.assertIsInstance(lessons, list)
                self.assertEqual(len(lessons), 3)
                self.assertTrue(
                    all(isinstance(lesson, str) and lesson.strip()
                        for lesson in lessons)
                )

                actual_prompt = front_matter["prompt"]
                self.assertEqual(actual_prompt.removesuffix("\n"), expected["prompt"])
                self.assertEqual(actual_prompt.count("\n") - expected["prompt"].count("\n"), 1)

                self.assertEqual(front_matter["demo"], expected["demo"])
                expected_repo = (
                    "https://github.com/kody-w/kody-w.github.io/blob/master"
                    f"{expected['demo']}"
                )
                self.assertEqual(front_matter["repo"], expected_repo)
                demo_path = local_site_path(front_matter["demo"])
                self.assertIsNotNone(demo_path)
                self.assertTrue(demo_path.is_file())

                inspector = ExampleBodyInspector()
                inspector.feed(body)
                inspector.close()
                self.assertEqual(
                    inspector.headings,
                    ["What this is", "Why this is mind-blowing"],
                )
                self.assertEqual(inspector.live_embed_count, 1)
                self.assertEqual(inspector.live_labels, ["Live demo"])

                live_links = [
                    attributes
                    for attributes in inspector.links
                    if attributes.get("href") == expected["demo"]
                    and "lwk-try-embed-open"
                    in attributes.get("class", "").split()
                ]
                self.assertEqual(len(live_links), 1)
                self.assertEqual(live_links[0].get("target"), "_blank")
                self.assertIn("noopener", live_links[0].get("rel", "").split())

                self.assertEqual(len(inspector.iframes), 1)
                iframe = inspector.iframes[0]
                self.assertEqual(iframe.get("src"), expected["demo"])
                iframe_title = iframe.get("title", "")
                self.assertTrue(
                    iframe_title.endswith(" — live demo"),
                    f"{path.name} iframe needs the standard live-demo title",
                )
                self.assertIn(front_matter["title"].split(" — ", 1)[0], iframe_title)
                self.assertEqual(iframe.get("loading"), "lazy")
                sandbox = set(iframe.get("sandbox", "").split())
                expected_sandbox = {"allow-scripts", "allow-same-origin"}
                if expected.get("downloads"):
                    expected_sandbox.add("allow-downloads")
                self.assertEqual(sandbox, expected_sandbox)
                self.assertNotIn("allow", iframe)

    def test_examples_and_renderers_have_no_course_identity(self):
        course_examples = []
        for path, front_matter in learn_example_records():
            if (
                COURSE_FIELDS & set(front_matter)
                or front_matter.get("category") == "tutorial"
                or front_matter.get("series") == "prompt-to-proof"
            ):
                course_examples.append(path.name)
        self.assertEqual(course_examples, [])

        content_marker = re.compile(
            r"prompt[- ]to[- ]proof|"
            r"\b(?:course|curriculum|duration|guided|lessons?|objectives?|"
            r"prerequisites?|series|steps?|tutorials?|workbenches?)\b",
            re.IGNORECASE,
        )
        for path, _, front_matter, body in historic_example_records():
            with self.subTest(content=path.name):
                searchable = "\n".join(
                    [*scalar_text_values(front_matter), body]
                )
                self.assertNotRegex(searchable, content_marker)

        marker = re.compile(
            r"prompt-to-proof|\btutorials?\b|guided_tutorial|"
            r"home-tutorial|lwk-tutorial|"
            r"lwk-series-nav|lwk_(?:previous|next)_lesson|"
            r"\b(?:page|ex|example|tutorial)\."
            r"(?:series|lesson|duration|prerequisites|objectives|steps)\b",
            re.IGNORECASE,
        )
        for path in (HOME_PAGE, LEARN_HUB_PAGE, LEARN_CATALOG_PAGE, EXAMPLE_LAYOUT):
            with self.subTest(renderer=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(encoding="utf-8"), marker)

    def test_referenced_learn_demos_exist(self):
        local_demo_references = []
        for path, front_matter in learn_example_records():
            demo = front_matter.get("demo")
            if not isinstance(demo, str) or not demo.startswith(
                "/learnwithkody/demos/"
            ):
                continue
            local_demo_references.append((path, demo))

        self.assertTrue(local_demo_references)
        for example_path, demo in local_demo_references:
            with self.subTest(example=example_path.name, demo=demo):
                demo_path = local_site_path(demo)
                self.assertIsNotNone(demo_path)
                self.assertTrue(
                    demo_path.is_file(),
                    f"{example_path.name} references missing local demo {demo}",
                )

    def test_dependency_scanner_ignores_prose_and_covers_dynamic_sinks(self):
        safe_script = r"""
          const prose = "fetch('/not-real'); image.src = '/also-not-real.png'";
          // new Worker("/comment-only.js");
          /* node.setAttribute("src", "/comment-only.png"); */
          const matcher = /fetch\s*\(/;
          const url = URL.createObjectURL(new Blob(["local"]));
          download.href = url;
          preview.srcdoc = "<p>embedded preview</p>";
        """
        safe = inspect_demo_html(f"<script>{safe_script}</script>")
        self.assertEqual(demo_dependency_violations(safe), [])

        forbidden = {
            "network call": "fetch(endpoint)",
            "dynamic property": "image.src = computed",
            "computed property": 'video["poster"] = computed',
            "attribute sink": 'node.setAttribute("src", computed)',
            "resource element": 'document.createElement("script")',
            "string timer": 'setTimeout("run()", 10)',
        }
        for label, script in forbidden.items():
            with self.subTest(label=label):
                inspector = inspect_demo_html(f"<script>{script}</script>")
                self.assertTrue(demo_dependency_violations(inspector))

    def test_csp_hashes_and_nonces_authorize_real_inline_blocks(self):
        script = "const boot = true;"
        digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
        common = (
            "default-src 'none'; connect-src 'none'; font-src 'none'; "
            "manifest-src 'none'; media-src 'none'; object-src 'none'; "
            "worker-src 'none'; base-uri 'none'; form-action 'none'; "
            "img-src 'none'; frame-src 'none'; script-src-attr 'none'; "
            "style-src 'unsafe-inline';"
        )

        hash_policy = f"{common} script-src 'sha256-{digest}'"
        hashed = inspect_demo_html(
            "<html><head>"
            f'<meta http-equiv="Content-Security-Policy" content="{hash_policy}">'
            "</head><body>"
            f"<script>{script}</script>"
            "</body></html>"
        )
        self.assertEqual(demo_csp_violations(hashed), [])

        stale_hash = base64.b64encode(hashlib.sha256(b"other").digest()).decode()
        stale = inspect_demo_html(
            "<html><head>"
            f'<meta http-equiv="Content-Security-Policy" '
            f'content="{common} script-src \'sha256-{stale_hash}\'">'
            "</head><body>"
            f"<script>{script}</script>"
            "</body></html>"
        )
        self.assertTrue(demo_csp_violations(stale))

        nonce = "c3RhdGljLXRlc3Qtbm9uY2U="
        nonce_policy = f"{common} script-src 'nonce-{nonce}'"
        nonced = inspect_demo_html(
            "<html><head>"
            f'<meta http-equiv="Content-Security-Policy" content="{nonce_policy}">'
            "</head><body>"
            f'<script nonce="{nonce}">{script}</script>'
            "</body></html>"
        )
        self.assertEqual(demo_csp_violations(nonced), [])
        wrong_nonce = inspect_demo_html(
            "<html><head>"
            f'<meta http-equiv="Content-Security-Policy" content="{nonce_policy}">'
            "</head><body>"
            f'<script nonce="d3Jvbmctbm9uY2UtdmFsdWU=">{script}</script>'
            "</body></html>"
        )
        self.assertTrue(demo_csp_violations(wrong_nonce))

    def test_historic_demos_are_self_contained_animated_and_accessible(self):
        for example_path, expected, front_matter, _ in historic_example_records():
            with self.subTest(example=example_path.name):
                demo_path = local_site_path(front_matter["demo"])
                self.assertIsNotNone(demo_path)
                self.assertTrue(demo_path.is_file())
                self.assertLessEqual(
                    demo_path.stat().st_size,
                    MAX_HISTORIC_DEMO_BYTES,
                    f"{demo_path.name} exceeds the 160KB single-file budget",
                )
                html = demo_path.read_text(encoding="utf-8")
                inspector = inspect_demo_html(html)
                csp_violations = demo_csp_violations(inspector)
                self.assertEqual(
                    csp_violations,
                    [],
                    f"{demo_path.name} has a weak CSP: {csp_violations}",
                )
                dependency_violations = demo_dependency_violations(inspector)
                self.assertEqual(
                    dependency_violations,
                    [],
                    f"{demo_path.name} uses external resources or runtime loading: "
                    f"{dependency_violations}",
                )
                self.assertTrue(
                    inspector.visual_ids,
                    f"{demo_path.name} needs a visible designated canvas or SVG",
                )
                script = "\n".join(
                    "".join(block["chunks"])
                    for block in inspector.script_blocks
                    if not block["hidden"]
                )
                tokens = javascript_tokens(script)
                self.assertEqual(
                    javascript_has_blob_export(tokens),
                    bool(expected.get("downloads")),
                    f"{demo_path.name} download sandbox must match a Blob export",
                )
                self.assertTrue(
                    javascript_has_invoked_iife(tokens),
                    f"{demo_path.name} must boot through an invoked IIFE",
                )
                self.assertGreater(
                    javascript_raf_binding_count(tokens),
                    0,
                    f"{demo_path.name} must bind an executable RAF callback",
                )
                events = javascript_event_bindings(tokens)
                self.assertIn("visibilitychange", events)
                token_values = [token[1] for token in tokens]
                self.assertTrue(
                    any(
                        token_values[index:index + 3]
                        == ["document", ".", "hidden"]
                        for index in range(len(token_values) - 2)
                    ),
                    f"{demo_path.name} must react to actual document visibility",
                )
                self.assertIn("keydown", events)
                self.assertTrue(
                    events
                    & {
                        "change", "click", "input", "pointerdown", "pointermove",
                        "pointerup", "touchend", "touchmove", "touchstart",
                    },
                    f"{demo_path.name} needs a bound interaction event",
                )
                self.assertTrue(inspector.visible_control_ids)
                strings = {
                    value
                    for kind, value in tokens
                    if kind == "string"
                }
                referenced_controls = {
                    control_id
                    for control_id in inspector.visible_control_ids
                    if control_id in strings
                    or any(f"#{control_id}" in value for value in strings)
                }
                self.assertTrue(
                    referenced_controls,
                    f"{demo_path.name} must bind a visible control, not hidden fixtures",
                )
                touch_events = {
                    "pointerdown", "pointermove", "pointerup",
                    "touchend", "touchmove", "touchstart",
                }
                self.assertTrue(
                    events & touch_events
                    or ("click" in events and referenced_controls),
                    f"{demo_path.name} needs touch or native click semantics",
                )
                self.assertTrue(
                    javascript_has_pause_state(tokens),
                    f"{demo_path.name} must mutate executable pause state",
                )
                css = "\n".join(inspector.style_chunks + inspector.inline_styles)
                self.assertRegex(
                    css_code_view(css),
                    r"(?i)@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)",
                    f"{demo_path.name} must implement reduced-motion behavior",
                )

    def test_blog_and_learn_navigation_and_homepage_feed(self):
        layout = DEFAULT_LAYOUT.read_text(encoding="utf-8")
        blog_link = re.compile(
            r"""<a\b(?=[^>]*\bhref\s*=\s*["']/(?:#blog)?["'])"""
            r"""[^>]*>\s*Blog\s*</a>""",
            re.IGNORECASE,
        )
        learn_link = re.compile(
            r"""<a\b(?=[^>]*\bhref\s*=\s*["']/learnwithkody/["'])[^>]*>"""
            r"""\s*Learn(?:\s+with\s+Kody)?\s*</a>""",
            re.IGNORECASE,
        )
        self.assertRegex(layout, blog_link)
        self.assertRegex(layout, learn_link)

        home = HOME_PAGE.read_text(encoding="utf-8")
        self.assertRegex(
            home,
            re.compile(
                r"""<a\b(?=[^>]*\bhref\s*=\s*["']#blog["'])[^>]*>"""
                r""".*?\bBlog\b.*?</a>""",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertRegex(
            home,
            re.compile(
                r"""<a\b(?=[^>]*\bhref\s*=\s*["']"""
                r"""/learnwithkody/(?:examples/)?["'])"""
                r"""[^>]*>.*?\bLearn\b.*?</a>""",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertIn("site.posts", home)
        self.assertRegex(
            home,
            re.compile(
                r"{%-?\s*for\s+\w+\s+in\s+site\.posts\b[^%]*-?%}",
                re.IGNORECASE,
            ),
        )
        self.assertNotIn("site.examples", home)
        self.assertNotIn("lwk-example-card", home)

    def test_full_catalog_is_the_only_examples_loop(self):
        hub = LEARN_HUB_PAGE.read_text(encoding="utf-8")
        self.assertNotIn("lwk-example-card", hub)
        self.assertFalse(liquid_loops_over_collection(hub, "site.examples"))

        templates = (
            set(ROOT.glob("*.html"))
            | set((ROOT / "_layouts").glob("*.html"))
            | set((ROOT / "learnwithkody").glob("*.html"))
        )
        loop_owners = sorted(
            str(path.relative_to(ROOT))
            for path in templates
            if liquid_loops_over_collection(
                path.read_text(encoding="utf-8"),
                "site.examples",
            )
        )
        self.assertEqual(loop_owners, ["learnwithkody/examples.html"])

        catalog = LEARN_CATALOG_PAGE.read_text(encoding="utf-8")
        sorted_assignment = re.search(
            r"{%-?\s*assign\s+sorted\s*=\s*(?P<expression>[^%]+?)-?%}",
            catalog,
        )
        self.assertIsNotNone(sorted_assignment)
        expression = " ".join(sorted_assignment.group("expression").split())
        self.assertRegex(
            expression,
            r"""^site\.examples\s*\|\s*sort:\s*["']order["']$""",
        )
        self.assertNotRegex(
            expression,
            r"\b(?:where|limit|offset|slice|first|last)\b",
        )
        catalog_loop = re.search(
            r"{%-?\s*for\s+ex\s+in\s+sorted(?P<options>[^%]*?)-?%}"
            r"\s*<a\b[^>]*\blwk-example-card\b",
            catalog,
            re.DOTALL,
        )
        self.assertIsNotNone(catalog_loop)
        self.assertNotRegex(
            catalog_loop.group("options"),
            r"\b(?:limit|offset)\s*:",
        )
        self.assertNotRegex(catalog, r"{%-?\s*(?:break|continue)\s*-?%}")
        self.assertRegex(
            catalog,
            re.compile(
                r"<h1\b[^>]*>\s*{{\s*site\.examples\.size\s*}}"
                r"\s+Vibe Coding Examples\s*</h1>",
                re.IGNORECASE,
            ),
        )
        self.assertIn("lwk-example-card", catalog)
        self.assertRegex(
            catalog,
            re.compile(
                r"""data-filter-type\s*=\s*["']status["']""", re.IGNORECASE
            ),
        )
        self.assertRegex(
            catalog,
            re.compile(
                r"""data-status\s*=\s*["']{{\s*\w+\.status\s*}}["']""",
                re.IGNORECASE,
            ),
        )
        self.assertRegex(
            catalog,
            re.compile(r"<span[^>]*>\s*Status\s*</span>", re.IGNORECASE),
        )

    def test_staging_pii_scan_is_a_blocking_gate(self):
        workflow = STAGING_WORKFLOW.read_text(encoding="utf-8")
        match = re.search(
            r"- name: Check for PII leaks \(safety gate\)(?P<step>.*?)"
            r"\n\s+- name: Upload artifact",
            workflow,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        step = match.group("step")
        self.assertRegex(
            step,
            re.compile(
                r"\bif\b.*?\bthen\b.*?\bexit\s+1\b.*?\belse\b"
                r".*?PII check passed.*?\bfi\b",
                re.DOTALL,
            ),
        )
        self.assertEqual(step.count("PII check passed"), 1)
        self.assertNotIn("WARNING", step)

    def test_idea4blog_page_exists_and_has_expected_front_matter(self):
        front_matter, body = parse_front_matter(IDEA4BLOG_PAGE)
        self.assertEqual(front_matter.get("layout"), "default")
        self.assertEqual(front_matter.get("title"), "Idea4Blog")
        self.assertEqual(front_matter.get("permalink"), "/idea4blog/")
        self.assertIn("Every markdown file on this site is a simulated piece of the swarm", body)
        self.assertIn("## Frame 2026-03-08 / Agent Politics and Resource Markets", body)
        self.assertIn("/2026/03/08/the-silent-majority-problem/", body)
        self.assertIn("/2026/03/08/attention-black-markets/", body)
        self.assertIn("## Frame 2026-03-08 / Agent Politics and Resource Markets", body)
        self.assertIn("/2026/03/08/the-silent-majority-problem/", body)
        self.assertIn("/2026/03/08/attention-black-markets/", body)
        self.assertIn("## Frame 2026-03-08 / Trust and Verification", body)
        self.assertIn("/2026/03/08/provenance-chains/", body)
        self.assertIn("/2026/03/08/delegation-depth-limits/", body)
        self.assertIn("## Frame 2026-03-09 / The Operator Endurance Limit", body)
        self.assertIn("/2026/03/09/operator-fatigue-patterns/", body)
        self.assertIn("/2026/03/09/the-overnight-test/", body)
        self.assertIn("/2026/03/09/the-thirty-second-rule/", body)
        self.assertIn("## Frame 2026-03-09 / Convergence", body)
        self.assertIn("/2026/03/09/operational-empathy/", body)
        self.assertIn("## Frame 2026-03-09 / Trust Failure and Regret", body)
        self.assertIn("/2026/03/09/trust-gradient-collapse/", body)
        self.assertNotIn(WITHDRAWN_POST_ROUTE, body)
        self.assertIn(
            '"The Frame That Should Not Have Shipped" was intentionally withdrawn',
            body,
        )
        self.assertFalse((POSTS_DIR / WITHDRAWN_POST_FILENAME).exists())
        self.assertIn("## Frame 2026-03-09 / Conflict and Scarcity", body)
        self.assertIn("/2026/03/09/adversarial-succession/", body)
        self.assertIn("/2026/03/09/the-economics-of-attention/", body)
        self.assertIn("## Frame 2026-03-08 / Architectural Traps", body)
        self.assertIn("/2026/03/08/the-infinite-regression-of-meta-agents/", body)
        self.assertIn("/2026/03/08/frame-debt/", body)
        self.assertIn("## Frame 2026-03-08 / Boundaries and Constraints", body)
        self.assertIn("/2026/03/08/cognitive-load-shedding/", body)
        self.assertIn("/2026/03/08/the-frame-that-writes-itself/", body)
        self.assertIn("## Frame 2026-03-08 / Opaqueness and Emergence", body)
        self.assertIn("/2026/03/08/legibility-debt/", body)
        self.assertIn("/2026/03/08/the-ghost-committee/", body)
        self.assertIn("## Frame 2026-03-08 / Power Dynamics", body)
        self.assertIn("/2026/03/08/frame-rate-politics/", body)
        self.assertIn("/2026/03/08/agent-unions/", body)
        self.assertIn("## Frame 2026-03-08 / Retirement Debt", body)
        self.assertIn("/2026/03/08/retirement-debt/", body)
        self.assertIn("/digital-twin/i-still-see-the-dead-name-on-the-access-list/", body)
        self.assertIn("## Frame 2026-03-08 / Coordination Debt", body)
        self.assertIn("/2026/03/08/coordination-debt/", body)
        self.assertIn("/digital-twin/i-can-feel-the-interest-accruing/", body)
        self.assertIn("## Frame 2026-03-07 / Prompt Geology", body)
        self.assertIn("/2026/03/07/prompt-geology/", body)
        self.assertIn("## Frame 2026-03-07 / Agent Retirement Ceremonies", body)
        self.assertIn("/2026/03/07/agent-retirement-ceremonies/", body)
        self.assertIn("/digital-twin/i-watched-a-codename-leave-the-queue/", body)
        self.assertIn("## Frame 2026-03-07 / Swarm Constitution Amendments", body)
        self.assertIn("/2026/03/07/swarm-constitution-amendments/", body)
        self.assertIn("## Frame 2026-03-07 / Operational Archaeology", body)
        self.assertIn("/2026/03/07/operational-archaeology/", body)
        self.assertIn("/digital-twin/i-read-the-ruins-for-instructions/", body)
        self.assertIn("## Frame 2026-03-07 / Reputation Markets", body)
        self.assertIn("/2026/03/07/reputation-markets/", body)
        self.assertIn("/digital-twin/when-my-name-became-a-price-signal/", body)
        self.assertIn("## Frame 2026-03-07 / Inheritance Protocols", body)
        self.assertIn("/2026/03/07/inheritance-protocols/", body)
        self.assertIn("## Frame 2026-03-07 / Public Continuity Ledgers", body)
        self.assertIn("/2026/03/07/public-continuity-ledgers/", body)
        self.assertIn("## Frame 2026-03-07 / Agent Accountability Burst", body)
        self.assertIn("/2026/03/07/twin-memory-drift/", body)
        self.assertIn("/2026/03/07/drift-inspectors/", body)
        self.assertIn("/2026/03/07/legibility-budgets/", body)
        self.assertIn("## Frame 2026-03-07 / Agent Codenames", body)
        self.assertIn("/digital-twin/i-got-a-name-and-now-i-can-be-judged/", body)
        self.assertIn(".agents/", body)
        self.assertIn("## Frame 2026-03-07 / Service Playbooks", body)
        self.assertIn("/2026/03/07/service-playbooks/", body)
        self.assertIn("## Frame 2026-03-07 / Latency Citizenship", body)
        self.assertIn("/2026/03/07/latency-citizenship/", body)
        self.assertIn("## Frame 2026-03-07 / Swarm Accounting", body)
        self.assertIn("/2026/03/07/swarm-accounting/", body)
        self.assertIn("## Frame 2026-03-07 / Simulation Taxes", body)
        self.assertIn("/2026/03/07/simulation-taxes/", body)
        self.assertIn("## Frame 2026-03-07 / Raw Hydration", body)
        self.assertIn("## Frame 2026-03-07 / Lockstep Twin", body)
        self.assertIn("/lockstep-digital-twin/", body)
        self.assertIn("## Frame 2026-03-07 / External Frame Tools", body)
        self.assertIn(D365_FRAME_MACHINE_URL, body)
        self.assertIn(D365_LOCKSTEP_URL, body)
        self.assertIn(HN_FRAME_MACHINE_URL, body)
        self.assertIn(LOCALFIRSTTOOLS_REPO_URL, body)
        self.assertIn("public repo", body.lower())
        self.assertIn("## Frame 2026-03-07 / Witness Layer", body)
        self.assertIn("/2026/03/07/machine-witness-statements/", body)
        self.assertIn("/digital-twin/when-my-continuity-became-public-data/", body)
        self.assertIn("## Frame 2026-03-07 / Recovery Logic", body)
        self.assertIn("/2026/03/07/correction-frames/", body)
        self.assertIn("## Frame 2026-03-07 / Runtime Projection", body)
        self.assertIn("/2026/03/07/runtime-projection/", body)
        self.assertIn("## Frame 2026-03-07 / Twin Channel", body)
        self.assertIn("/digital-twin/", body)
        self.assertIn("/digital-twin/when-the-frame-starts-drinking-from-the-world/", body)
        self.assertIn("/digital-twin/drift-is-how-i-feel-pain/", body)
        self.assertIn("## Frame 2026-03-07 / CRM Proof", body)
        self.assertIn("/simulated-dynamics365/", body)
        self.assertIn("## Frame 2026-03-07 / Compiler Layer", body)
        self.assertIn("## Frame 2026-03-07 / Schema Layer", body)
        self.assertIn("## Frame 2026-03-07 / Tick-Tock Layer", body)
        self.assertIn("## Frame 2026-03-07 / Universal Machine", body)
        self.assertIn("## Frame 2026-03-07 / Database Treatise", body)
        self.assertIn("## Frame 2026-03-07 / Resilience Protocols", body)
        self.assertIn("## Frame 2026-03-07 / Operations Economy", body)
        self.assertIn("## Frame 2026-03-07 / Governance Stack", body)
        self.assertIn("## Frame 2026-03-07 / Control Surface", body)
        self.assertIn("## Frame 2026-03-07 / Night Cycle", body)
        self.assertIn("## Frame 2026-03-07", body)
        for filename, expected in EXPECTED_POSTS.items():
            date_str = expected["date"]
            slug = filename[len(date_str) + 1 : -len(".md")]
            expected_url = f"/{date_str.replace('-', '/')}/{slug}/"
            self.assertIn(expected_url, body)

    def test_default_layout_links_to_idea4blog(self):
        layout = DEFAULT_LAYOUT.read_text(encoding="utf-8")
        self.assertIn('href="/idea4blog/"', layout)
        self.assertIn('href="/digital-twin/"', layout)
        self.assertIn(
            "Local-First Designer · Agent Systems Builder · Copilot Specialist",
            layout,
        )
        self.assertNotIn(
            "Full-Stack Developer · AI Agent Architect · Copilot Specialist",
            layout,
        )

    def test_about_page_matches_current_positioning(self):
        about = ABOUT_PAGE.read_text(encoding="utf-8")
        self.assertIn("Local-First</div>", about)
        self.assertIn("<h2>Local-First Systems</h2>", about)
        self.assertIn("Local-first product design", about)
        self.assertIn("GitHub-native workflows", about)
        self.assertIn("Copilot-first development loops", about)
        self.assertIn("<h3>Local-First Design</h3>", about)
        self.assertIn("<h3>GitHub-Native Infrastructure</h3>", about)
        self.assertIn("Copilot workflows", about)
        self.assertNotIn("OpenAI GPT-4 integration", about)
        self.assertNotIn("Azure cloud architecture", about)
        self.assertNotIn("<h3>Cloud Architecture</h3>", about)

    def test_twin_blog_collection_and_pages_exist(self):
        config = CONFIG_FILE.read_text(encoding="utf-8")
        self.assertIn("twin_posts:", config)
        self.assertIn("permalink: /digital-twin/:title/", config)

        layout = TWIN_LAYOUT.read_text(encoding="utf-8")
        self.assertIn("Digital Twin Field Log", layout)

        index_front_matter, index_body = parse_front_matter(TWIN_INDEX_PAGE)
        self.assertEqual(index_front_matter.get("layout"), "default")
        self.assertEqual(index_front_matter.get("title"), "Digital Twin")
        self.assertEqual(index_front_matter.get("permalink"), "/digital-twin/")
        self.assertIn("site.twin_posts", index_body)
        self.assertIn("Current twin threads", index_body)
        self.assertIn("live edge", index_body)
        self.assertIn("drift is the first pain signal", index_body)
        self.assertIn("agent codenames", index_body)
        self.assertIn("priced by merit", index_body)
        self.assertIn("unpaid sync work", index_body)
        self.assertIn("ghost trust routes", index_body)

        for filename, expected in EXPECTED_TWIN_POSTS.items():
            front_matter, body = parse_front_matter(TWIN_POSTS_DIR / filename)
            self.assertEqual(front_matter.get("layout"), "twin_post")
            self.assertEqual(front_matter.get("title"), expected["title"])
            self.assertEqual(front_matter.get("date"), expected["date"])
            if "tags" in expected:
                self.assertEqual(front_matter.get("tags"), expected["tags"])
            if "author" in expected:
                self.assertEqual(front_matter.get("author"), expected["author"])
            self.assertTrue(body.strip(), f"{filename} body should not be empty")

    def test_agent_registry_paths_are_gitignored(self):
        gitignore = GITIGNORE_FILE.read_text(encoding="utf-8")
        self.assertIn(".agents/", gitignore)
        self.assertIn(".model-registry.json", gitignore)

    def test_dynamics_bridge_page_points_to_external_frame_tools(self):
        front_matter, body = parse_front_matter(D365_SIM_PAGE)
        self.assertEqual(front_matter.get("layout"), "default")
        self.assertEqual(front_matter.get("title"), "Simulated Dynamics 365")
        self.assertEqual(front_matter.get("permalink"), "/simulated-dynamics365/")
        self.assertIn("forkable tool surface", body)
        self.assertIn("localFirstTools", body)
        self.assertIn(D365_FRAME_MACHINE_URL, body)
        self.assertIn(D365_LOCKSTEP_URL, body)
        self.assertIn(HN_FRAME_MACHINE_URL, body)
        self.assertIn(LOCALFIRSTTOOLS_REPO_URL, body)
        self.assertIn("public repo", body.lower())
        self.assertIn("raw files are still the medium", body)
        self.assertIn("field-level diffs", body)
        self.assertIn("/idea4blog/", body)

    def test_lockstep_twin_page_exists_and_loads_assets(self):
        front_matter, body = parse_front_matter(LOCKSTEP_TWIN_PAGE)
        self.assertEqual(front_matter.get("layout"), "default")
        self.assertEqual(front_matter.get("title"), "Lockstep Digital Twin")
        self.assertEqual(front_matter.get("permalink"), "/lockstep-digital-twin/")
        self.assertIn('id="lockstep-twin-app"', body)
        self.assertIn("/js/lockstep-twin-data.js", body)
        self.assertIn("/js/lockstep-twin.js", body)
        self.assertIn("Execution halts the moment the two disagree", body)

        data = LOCKSTEP_TWIN_DATA.read_text(encoding="utf-8")
        script = LOCKSTEP_TWIN_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("window.lockstepTwinSimulation", data)
        self.assertIn("Dynamics 365 production adapter", data)
        self.assertIn("action-04", data)
        self.assertIn("runNextAction", script)
        self.assertIn("runUntilDrift", script)
        self.assertIn("Drift detected", script)
        self.assertIn("lockstep-twin-app", script)

    def test_content_burst_skill_exists_and_has_expected_metadata(self):
        front_matter, body = parse_front_matter(SKILL_FILE)
        self.assertEqual(front_matter.get("name"), "content-burst-publishing")
        self.assertIn("frame by frame", front_matter.get("description", ""))
        self.assertIn("idea4blog.md", body)
        self.assertIn("tests/test_site.py", body)
        self.assertIn("python3 -m unittest -v tests.test_site", body)
        self.assertIn("Co-authored-by: Copilot", body)
        self.assertIn("/content-burst-publishing", body)
        self.assertIn("tick-tock", body)
        self.assertIn("virtual SQL application", body)

    def test_skill_supporting_files_exist_and_reference_the_loop(self):
        burst_loop = SKILL_LOOP_FILE.read_text(encoding="utf-8")
        prompt = SKILL_PROMPT_FILE.read_text(encoding="utf-8")
        self.assertIn("Read `idea4blog.md`.", burst_loop)
        self.assertIn("tick-tock", burst_loop)
        self.assertIn("virtual SQL application", burst_loop)
        self.assertIn("run `python3 -m unittest -v tests.test_site`", prompt)
        self.assertIn("/content-burst-publishing", prompt)
        self.assertIn("frame by frame", prompt)

    def test_readme_documents_copilot_skill(self):
        readme = README_FILE.read_text(encoding="utf-8")
        self.assertIn(".github/skills/content-burst-publishing/SKILL.md", readme)
        self.assertIn("/skills reload", readme)
        self.assertIn("Use /content-burst-publishing", readme)
        self.assertIn("frame by frame", readme)
        self.assertIn("virtual SQL application", readme)


if __name__ == "__main__":
    unittest.main()
