# Microsoft 365 Team Dashboard

Per-operator workflow dashboard. Self-contained HTML over the existing brainstem agents — no LLM in the hydration path, no separate dashboard logic.

In your local brainstem chat:

```
DashboardRender
```

The agent calls `ProjectPinger`, `Twin`, `Pm` with static inputs (no LLM in the loop), renders everything into one self-contained HTML file at `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/dashboard.html`, and returns the path. Open the path in your browser. Re-run + refresh to update.
