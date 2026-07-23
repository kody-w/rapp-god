# Target tool inputs

Target-owned tools contain no workstation, session-ID, or temporary-directory
defaults. External evidence is supplied explicitly or through `RAPP_GOD_*`
environment variables. Repo-local defaults live only below ignored
`.rapp-god-input/`.

| Tool | Input |
|---|---|
| `tools/assimilation.py import` | `--cache` or `RAPP_GOD_SOURCE_CACHE`; default `.rapp-god-input/sources` |
| `tools/native_provenance.py` | `--source-cache` or `RAPP_GOD_SOURCE_CACHE` |
| `tools/archive_inventory.py scan-source` | required `--source-cache`, `--output`, `--captured-at` |
| `tools/archive_inventory.py generate` | required `--evidence`; optional `--check` |
| `tools/ref_inventory.py` | explicit evidence files plus collection start/end; sensitive regeneration also requires the session artifact and expected digest |
| rapp-map wrapper | Python path from `RAPP_GOD_PYTHON312` |
| UltraCode wrapper | Python path from `RAPP_GOD_PYTHON311` |

Generators support `--check` (or a check subcommand) and perform no network
activity in check mode. Session-only quarantine inputs must never be copied,
logged, staged, or named in public output.
