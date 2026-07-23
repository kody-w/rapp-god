# RAPP drift lint

Per-commit reflexes for invariant drift across the RAPP estate. The linter is
regex-grade, deterministic, zero-LLM, and has no package dependencies.

## Rules

- **R1:** rejects minting or teaching language on lines containing legacy
  `rappid:v2:` or `rappid:v3:` forms unless the same line says `legacy`,
  `read-forever` (or `read forever`), or `canonicalized`.
  Teaching vocabulary covers the `mint`, `emit`, `teach`, `use`, `format`,
  `syntax`, `grammar`, `create`, `generate`, `issue`, `produce`, `write`,
  `construct`, `assign`, `prefix`, `template`, `example`, and `new` families.
- **R2:** rejects the obsolete `Prototyping` + `Platform` expansion. The canon is
  `Prototype Platform`.
- **R3:** twin-pins any sibling `ecosystem-spec.json` and `ECOSYSTEM_SPEC.md`.
  Changing exactly one in the selected commit range fails.
- **R4:** rejects the case-insensitive work-account stem `kowi` + `ldfe` and
  email addresses at the `microsoft.com` and `gmail.com` domains.

Only Git-tracked UTF-8 text is scanned. Binary files, `.git`, `node_modules`,
and historical JSON beneath any `frames/` directory are skipped.

## Run locally

Node 20 or newer is required:

```bash
node lint.mjs
node /path/to/lint.mjs --path /path/to/repository
```

R3 compares `GITHUB_BASE...HEAD` when `GITHUB_BASE` is set and otherwise
compares `HEAD~1...HEAD`. Repositories without a usable parent have no R3 diff.
Every violation is written as `file:line: rule message`; any violation exits 1,
CLI/setup errors exit 2, and a clean scan exits 0.

## Adopt

Add `.github/workflows/drift-lint.yml` with these six lines:

```yaml
name: Drift lint
on: [push, pull_request]
permissions: { contents: read }
jobs:
  drift-lint:
    uses: kody-w/rapp-drift-lint/.github/workflows/drift-lint-reusable.yml@main
```
