# XBrief output schema

`xbrief prepare --json <url>` prints one JSON object to stdout. Schema version 2 adds `opportunities_path`:

```json
{
  "schema_version": 2,
  "run_id": "uuid",
  "tweet_id": "123",
  "outcome": "success",
  "stop_reason": "cursor_exhausted",
  "comments_fetched": 42,
  "compact_context_path": "/absolute/path/_data/compact-context.json",
  "analysis_prompt_path": "/absolute/path/_data/analysis-prompt.md",
  "opportunities_path": "/absolute/path/_data/opportunities.json",
  "report_path": "/absolute/path/index.md",
  "comments_index_path": "/absolute/path/comments.md",
  "warnings": []
}
```

Outcomes:

- `success`: the configured traversal completed.
- `partial`: usable comments were saved, but a cap, repeated cursor, rate limit, or backend failure interrupted traversal.
- `failure`: comments could not be fetched; do not produce a comment analysis.

`cursor_exhausted` means only that the upstream's visible pagination ended. Hidden, deleted, restricted, or differently ranked replies may still be absent.

Before Codex analysis, `opportunities_path` contains a valid schema-version-2 placeholder with `analysis_input_hash`, `status: "awaiting_analysis"`, an empty `opportunities` list, and `recommended_execution: null`. After analysis it preserves the same hash, contains `status: "analyzed"`, one JSON item for each opportunity card, and a `recommended_execution` object mirroring the personal execution plan in the Markdown report.

The hash is a SHA-256 fingerprint of normalized analysis-relevant post and reply fields. A prepare run preserves analysis only when the previous and current hashes match. If the evidence changes, XBrief replaces the analysis with the waiting marker and resets `opportunities.json` to `awaiting_analysis`, preventing stale conclusions from appearing current.
