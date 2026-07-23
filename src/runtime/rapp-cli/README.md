# RAPP CLI

The headless terminal control surface for RAPP. It operates an existing
Brainstem provider, chats through that provider's `/chat` endpoint, manages
integrity-checked agent cartridges, inspects release-train observations, and
materializes already-prepared local Twin folders, and reports unavailable
ecosystem surfaces honestly.

The CLI is a client and control plane. It does not vendor or modify
[`kody-w/rapp-installer`](https://github.com/kody-w/rapp-installer), execute ring
installers, or invent lifecycle behavior for specification-only products.

## Install

Python 3.11 or newer is required.

```console
pipx install git+https://github.com/kody-w/rapp-cli.git
```

After the first package release, `pipx install rapp-cli` installs from PyPI.

From a checkout:

```console
python3.13 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/rapp --version
```

The Brainstem remains independently installed. `rapp launch` runs a detected
Brainstem-compatible layout in the foreground; it never installs or updates it.

## Quickstart

```console
# Read-only shallow probe. /version does not load agent cartridges.
rapp status

# Run an already-installed Brainstem in the foreground.
rapp launch

# One-shot, piped, streaming, or interactive chat.
rapp chat "What agents are available?"
printf 'Reply only with ok' | rapp chat
rapp chat --stream "Explain the current workspace"
rapp --jsonl chat --stream "Explain the current workspace"
rapp chat

# Machine-readable output: global flags precede the command.
rapp --json status

# Hatch an already identity-bearing local Twin folder.
rapp twin hatch FOLDER --yes
rapp twin list
```

## Commands

| Command | Purpose |
|---|---|
| `rapp status` | Probe `/version` without loading agents |
| `rapp doctor [--offline\|--deep]` | Diagnose Python, configuration, and Brainstem reachability |
| `rapp capabilities` | Report implemented, read-only, and unavailable surfaces |
| `rapp launch` | Run a detected Brainstem-compatible layout in the foreground |
| `rapp brainstem locate` | Show the detected compatible layout, source, and Python |
| `rapp brainstem run` | Explicit form of `rapp launch` |
| `rapp brainstem health` | Deep `/health` inspection; may import installed agents |
| `rapp brainstem version` | Read the runtime version |
| `rapp chat [MESSAGE...]` | Use `/chat` or `/chat/stream`; no message reads stdin or starts a REPL |
| `rapp auth status\|login\|poll\|retry\|switch` | Operate Brainstem device-code authentication |
| `rapp model list\|set` | Inspect or select the Brainstem model |
| `rapp agent list` | List installed files; Brainstem may import cartridges |
| `rapp agent import\|export\|remove` | Manage local `*_agent.py` cartridges |
| `rapp agent search\|info\|install` | Use the CLI's integrity-pinned RAR compatibility snapshot |
| `rapp ring list\|status` | Inspect read-only release-train metadata observations |
| `rapp ring fly` | Fails explicitly until a sandbox contract is published |
| `rapp twin hatch FOLDER --yes [--home PATH]` | Materialize a prepared local Twin and register its agents |
| `rapp twin list\|show` | Safely inspect local Twin workspaces |
| `rapp twin legacy-list\|legacy-show` | Preserved aliases for historical local inspection |
| `rapp twin drive` | Fails explicitly; direct Twin driving is not implemented |
| `rapp config path\|show` | Show resolved, non-secret configuration |

Run `rapp <command> --help` for command-specific options.

## Twin hatch

`rapp twin hatch` **consumes** an already identity-bearing folder. It never
mints an identity, rewrites a rappid, reparents ancestry, scrapes or synthesizes
writings, or invents an egg-producer format. The minimum folder is:

```text
FOLDER/
├── rappid.json
├── soul.md
└── agents/
    └── example_agent.py
```

`rappid.json` must be a strict JSON object with `schema: "rapp/1"`, `kind:
"twin"` or `"organism"`, and a canonical
`rappid:@owner/slug:<64 lowercase hex>`. Optional `name` and `display_name`
values must be strings. Owner and slug are lowercase alphanumeric labels with
single interior hyphens only; owner is at most 39 characters and slug at most
100. `soul.md` must be non-empty UTF-8 text. `agents/` must contain at least
one immediate regular, non-symlink `*_agent.py` file, with no filenames that
collide under Unicode case folding. Additional safe files and
directories—including `frames/`, memory, provenance, and documentation—are
preserved byte-for-byte.

Because every bundled agent is executable Python when Brainstem imports it,
`--yes` is mandatory and is checked before the CLI reads the folder or contacts
Brainstem. The source is treated only as data by the CLI; the CLI never imports
agent modules itself.

The 64-hex rappid tail becomes the directory name under
`${RAPP_TWINS_HOME:-~/.rapp/twins}` (or `--home`). Hatching:

1. rejects symlinks, reparse points, special files, unsafe relative names,
   `.lineage_key`, `.copilot_token`, `.env`, and any `private` path component;
2. rejects any overlap where source, Twin home, or target contains another;
3. limits the folder to 4,096 files, 4,096 directories, 16 MiB per file, and
   256 MiB total;
4. hashes sorted normalized relative paths, entry types, and exact file bytes
   into a deterministic source-tree SHA-256;
5. copies into a private sibling staging directory, fsyncs where supported,
   and atomically installs without overwriting;
6. records a CLI-private receipt at
   `<home>/.receipts/<source-tree-sha256>.json`.

Overlap checks compare device/inode identity for existing paths and their
nearest existing ancestors, so case-variant aliases and nonexistent
descendants cannot bypass containment checks on case-insensitive filesystems.
An existing target is accepted only when its complete safe-tree digest is
identical. Receipts are not runtime inputs and `.receipts` is never listed as a
Twin. Agent filenames are capped at 255 ASCII bytes, and the generated receipt
is checked against a 2 MiB bound before local materialization; that bound
covers the maximum 4,096-agent shape, so every generated receipt remains
readable on retry. A per-identity advisory lock under `<home>/.locks/`
serializes cooperating `rapp-cli` hatch processes.

Local materialization and its receipt complete before provider registration.
The CLI then queries `/agents`. A filename collision is matched
case-insensitively; case-only spelling differences are conflicts, while exact
spelling, identical SHA-256, and at least one loaded agent name is reported as
`existing`. An existing file with an empty `agents` list remains a clear
provider failure. Missing agents are uploaded with their full SHA-256,
exported again, and followed by a fresh `/agents` query. They are reported as
`imported` only after exact post-import hash verification, an absent or `ok`
provider status, and a non-empty valid loaded-agent list.

Brainstem exposes unconditional import/delete routes without an ETag or
revision precondition. Therefore provider registration cannot be globally
atomic against non-CLI writers. If registration fails, the complete local
Twin, local-only receipt, and any provider files already imported remain for an
idempotent retry; hatch never automatically deletes an agent. The advisory
lock coordinates this CLI only and cannot constrain other Brainstem clients.
A retained byte-identical file that still fails to load remains a failure on
retry rather than being accepted as `existing`.

JSON results identify the `twin.hatch` command and include the endpoint plus
each agent's status, but never include soul text, agent source, secrets, or
arbitrary contact metadata. The live Brainstem discovers imported agents on
its next request, so no restart is required. Hatching does not select or force
an agent through `/chat`.

Secure source traversal uses verified directory descriptors, handle-relative
no-follow opens, deterministic ordering, and device/inode revalidation. Python
does not expose an equivalent guarantee on Windows, so Twin hatch currently
fails closed there rather than following a possible reparse-point swap.

`.egg` consumption, source adapters, summon/mint workflows, and direct Twin
driving are not yet implemented. `rapp twin drive` remains explicitly
unavailable.

## Configuration

Precedence is command flags, `RAPP_*` environment variables, the user config
file, then built-in defaults.

Default config location:

- Unix: `${XDG_CONFIG_HOME:-~/.config}/rapp/config.json`
- Windows: `%APPDATA%\rapp\config.json`
- Override: `RAPP_CONFIG_FILE`

Supported config:

```json
{
  "brainstem_url": "http://127.0.0.1:7071",
  "timeout": 30,
  "brainstem_secret_file": "~/.brainstem/src/rapp_brainstem/.brainstem_secret"
}
```

Environment equivalents:

| Variable | Meaning |
|---|---|
| `RAPP_ENDPOINT` / `RAPP_BRAINSTEM_URL` | Brainstem base URL |
| `RAPP_TIMEOUT` | Request timeout |
| `RAPP_BRAINSTEM_SECRET` | LAN secret |
| `RAPP_BRAINSTEM_SECRET_FILE` | Preferred path to a mode-`0600` secret |
| `RAPP_BRAINSTEM_HOME` | Brainstem-compatible installation root |
| `RAPP_TWINS_HOME` | Local twin workspace root |
| `RAPP_RELEASE_TRAIN_URL` | Release-train static API override |

Plaintext HTTP is accepted automatically only on loopback. A non-loopback HTTP
endpoint requires `--allow-insecure-http`; HTTPS is preferred.

## Machine output

`--json` emits exactly one `rapp-cli-result/1.0` or
`rapp-cli-error/1.0` document on stdout. Streaming commands use `--jsonl` and
emit `rapp-cli-event/1.0` records.

```json
{
  "schema": "rapp-cli-result/1.0",
  "ok": true,
  "command": "status",
  "data": {},
  "warnings": [],
  "meta": {"cli_version": "0.1.0"}
}
```

Exit codes are stable:

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Domain operation failure |
| `2` | Invalid usage or configuration |
| `3` | Capability is not published |
| `4` | Missing installation, connection failure, or timeout |
| `5` | Authentication or Copilot entitlement failure |
| `6` | Conflict or confirmation required |
| `7` | Upstream protocol or operation failure |
| `8` | Integrity or security refusal |
| `70` | Unexpected internal CLI failure |
| `130` | Interrupted |

## Trust and safety

- HTTP redirects are refused, response sizes are bounded, and non-loopback
  plaintext HTTP is opt-in.
- Secrets are never accepted as command-line values or printed by `config show`.
- `status` probes only `/version`. `/health`, `agent list`, and agent imports can
  cause Brainstem to import cartridge Python and are explicit commands.
- Local imports require a regular non-symlink `*_agent.py`, optional full
  SHA-256 verification, and `--yes`.
- Twin hatch applies bounded no-link tree validation, preserves safe bytes,
  installs transactionally, and requires exact local and Brainstem hashes for
  idempotency.
- RAR installs use a CLI compatibility pin matching the inspected Brainstem
  revision, verify the registry's full SHA-256, and provide integrity rather
  than identity or RAPP/1 trust.
- Ring operations are read-only. The CLI never executes downloaded installer
  text or promotes a release.
- Twin inspection never imports or executes files and never mutates lifecycle
  directories. Direct Twin driving remains unavailable.

See [SECURITY.md](SECURITY.md) for the security boundary.

## Development

```console
python3.13 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m build
```

Tests use local fixture servers and never call live inference.

## License

Code is released under the MIT License. RAPP and related names remain
trademarks of the RAPP project; see [LICENSE](LICENSE) and
[DISCLAIMER.md](DISCLAIMER.md).
