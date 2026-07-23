# Security

## Boundary

`rapp-cli` is a client for independently installed RAPP services. It does not
sandbox Brainstem agents: a `*_agent.py` loaded by Brainstem executes with the
Brainstem process user's privileges.

The CLI therefore:

- never imports agent Python itself;
- never modifies or embeds `rapp-installer`;
- refuses HTTP redirects and credential-bearing URLs;
- allows plaintext HTTP by default only on loopback;
- bounds JSON, stream, error, and agent payload sizes;
- accepts LAN secrets through environment variables or protected files, not
  command-line values;
- requires explicit confirmation for importing, installing, removing, or
  switching credentials;
- requires `--yes` before reading a Twin hatch source or contacting Brainstem;
- treats ring installers and static API command strings as data, never code;
- stops no process merely because it owns a port.

POSIX secret files must have mode `0600`. On Windows, the CLI rejects reparse
points but relies on the current account's filesystem ACLs; it does not attempt
to rewrite or certify those ACLs.

`rapp brainstem health`, `rapp doctor --deep`, and `rapp agent list` call
Brainstem routes that may import installed cartridges. Use the shallow
`rapp status` probe when inspecting an untrusted installation.

## Twin hatch boundary

`rapp twin hatch FOLDER --yes [--home PATH]` consumes a prepared folder; it
does not create identity or ancestry. The CLI does not import the folder's
Python, scrape or synthesize writings, or infer missing files. Brainstem does
execute each registered `*_agent.py` with the Brainstem process user's
privileges.

Before copying any source entry, the hatch scanner rejects:

- a symlink or filesystem reparse point at the source root or anywhere below
  it;
- sockets, devices, FIFOs, and every other special file;
- traversal-like or non-UTF-8 relative names;
- `.lineage_key`, `.copilot_token`, `.env`, or any `private` path component,
  at any depth.
- source/home/target containment in either direction.

Containment uses filesystem device/inode identity for existing paths and
nearest existing ancestors in addition to lexical resolution. Case-variant
aliases and nonexistent descendants therefore remain detectable on
case-insensitive filesystems.
On POSIX, traversal enumerates verified directory descriptors, opens every
child relative to its parent with no-follow flags, and revalidates device,
inode, type, and mutation metadata. A child swapped after enumeration is
rejected rather than followed. The Python standard library cannot provide the
same directory-handle guarantee for Windows reparse points, so hatch fails
closed on Windows. It allows at most 4,096 files and 4,096 directories, 16 MiB
per file, and 256 MiB total. `rappid.json` and `soul.md` receive strict UTF-8
semantic validation. Other accepted content remains inert data in the CLI and
is preserved exactly.

Materialization uses owner-only staging permissions, file and directory fsync
where supported, and an atomic no-overwrite rename. A pre-existing identity
directory succeeds only if its deterministic safe-tree SHA-256 is identical.
An advisory lock in private `.locks` serializes cooperating `rapp-cli`
processes for one identity. Local installation and a private `.receipts`
record complete before provider registration. Both control directories are
excluded from Twin listing. A receipt proves only local materialization and is
not trusted by the runtime or evidence that provider registration completed.
Receipt and JSON result fields contain hashes, identity, paths, endpoint, and
status only—not soul text, agent source, secrets, or arbitrary contact data
copied from metadata.

Brainstem registration first lists `/agents` and compares names under case
folding. Case-only spelling differences are conflicts. An exact matching name
is exported and compared by exact SHA-256, and its reported `agents` array must
contain at least one valid loaded-agent name. Missing payloads are sent with
the full SHA-256. `BrainstemClient.import_agent` computes boundaries, fields,
headers, filename, CRLF, and payload before joining and enforces the 16 MiB
limit against that complete multipart request. A present provider `status`
must be `ok`. Every successful import is exported and hash-verified, then
`/agents` is refreshed and must report the exact filename with a non-empty
valid loaded-agent list before hatch returns success.

Brainstem import and delete have no conditional-write revision or ETag, so no
client can make provider rollback atomic against non-CLI writers. Hatch never
automatically deletes an imported agent after failure: doing so could delete a
replacement written concurrently. Complete local state, its local-only
receipt, and any successfully imported provider files remain for idempotent
retry. The local advisory lock cannot constrain non-CLI Brainstem writers, and
a replacement can still race after post-import verification.

Generated receipts are size-checked before materialization. The 2 MiB receipt
read/write bound is larger than the maximum encoded 4,096-agent receipt under
the enforced 255-byte ASCII filename limit, preventing a successful first
hatch from becoming unreadable on retry.

No restart is requested: Brainstem hot-loads on its next request. Hatch does
not add a direct `/chat` selector and makes no forced-routing guarantee.
`.egg` consumption, source adapters, summon/mint behavior, and direct Twin
drive are not implemented.

## Reporting

Report vulnerabilities privately to the repository owner. Do not include
tokens, LAN secrets, `.env` files, private agent source, diagnostic exports, or
personal paths in a public issue.
