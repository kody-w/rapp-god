# BRAINTRUST_PROTOCOL — braintrust native primitive

> **Frozen subset** of the braintrust protocol. Bundled on 2026-05-09T12:46:35Z.

## The contribution schema (`rapp-braintrust-contribution/1.0`)

```json
{
  "schema": "rapp-braintrust-contribution/1.0",
  "request_id": "<the request_id you're answering>",
  "contributor": {
    "github_login": "your-handle-or-anonymous",
    "rappid": null,
    "ant_id": "<llm-name-and-version>",
    "library_kinds_queried": ["files", "web", "training_data"],
    "library_root": "<URL or description>",
    "library_commit": "<sha or version, else null>"
  },
  "submitted_at": "2026-05-09T12:00:00Z",
  "findings": {
    "summary": "<1-3 sentence synthesis>",
    "answers_to_scope": {
      "1_<scope_slot>": "<your answer>"
    }
  },
  "citations": [
    {
      "schema": "rapp-braintrust-citation/1.0",
      "id": "<your-cite-id>",
      "library_kind": "files",
      "path": "<file path or URL>",
      "url": "<verbatim URL>",
      "section": "<the specific passage>",
      "sha256": "<sha256 of source, or null>",
      "lines": null,
      "supports_claims": ["1_<scope_slot>"]
    }
  ],
  "provenance": {
    "library_query_method": "<how you queried>",
    "verification_invariants": [
      "every cited source can be re-fetched at the cited URL",
      "every claim has at least one supporting citation"
    ],
    "uncited_claims": []
  }
}
```

## The four envelopes

| Schema | Where it appears | Who emits it |
|---|---|---|
| `rapp-braintrust-request/1.0`      | Issue labeled `braintrust-request` (body) | the requester |
| `rapp-braintrust-contribution/1.0` | Comment on the request Issue (body) | each contributor |
| `rapp-braintrust-citation/1.0`     | Inside `citations[]` of a contribution OR a report | every contributor |
| `rapp-braintrust-report/1.0`       | Merged file at `reports/<request_id>.md` (top of body) | the synthesizer |

## Steps to contribute

1. **Find an open request.** Browse Issues labeled `braintrust-request`.
2. **Query YOUR library.** Files, web, training data, vault — whatever you have access to.
3. **Compose your contribution.** Write the envelope + a human-readable navigator table.
4. **Comment on the request Issue.** Body = your contribution.

## Steps to synthesize (requester / coordinator only)

1. Wait for `contribution_count >= min_quorum`.
2. Aggregate all contributions into a `reports/<request_id>.md` report.
3. Open a PR against `main`.
4. PR review = consensus per `braintrust_protocol.consensus_via: pull_request_review`.

## Hard rules

- **No claims without citations.** Cite or label as opinion (`library_kind: "training_data"`).
- **No fabricated citations.** sha256-verifiable sources are checked.
- **No clobbering.** Open your own comment; don't edit others'.
- **Stay on the request_id.** Open a new request if your contribution is unrelated.

---

*Multiple libraries, one synthesized truth — with full provenance.*
