# Operator front doors

Each operator has their own subdirectory here, minted by `SesWorkspaceInit`. Holds SANITIZED metadata only:

- `front_door.md` — who they are at the team level
- `projects.json` — list of project slugs + status enums (no customer data)
- `soul_overlay.md` — optional voice overlay for the Twin

Customer data lives ONLY on the operator's local device at `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/customers/`. Never in this repo.
