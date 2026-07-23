# Generated catalog

`components.jsonl`, `domains.json`, `test-plan.json`, and `indexes/` are
deterministic derivatives of the source lock and file ledger. Imported
workflows are indexed as `inactive-imported`; their presence does not activate
them or claim equivalence with root CI.

The capability index is `indexes/agents.jsonl`, following native RAPP
terminology.

Pass-two semantic views are fail closed: imported components default to
non-authoritative and non-runnable. `components.jsonl`,
`protocol-families.jsonl`, `agent-identities.jsonl`, `capabilities.jsonl`,
`identity-migrations.jsonl`, split workflow indexes, service topology, runtime
profiles, and the compatibility matrix carry explicit lifecycle/currentness
and ownership fields.

`indexes/ref-summary.jsonl` and `indexes/releases.jsonl` are compact views over
provenance metadata. They do not create branches, tags, releases, or assets.
