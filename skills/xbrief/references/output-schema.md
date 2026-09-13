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

When the source post embeds a readable X Article, the archive also contains `_data/article.json`, and the normalized article is nested under `post.article` in `compact-context.json`. The article body participates in the analysis hash, so adding, removing, or changing it invalidates stale analysis. If a short link is not an X Article or the article cannot be read, the post and replies are still archived and the returned `warnings` explain the bounded fallback.

Article media URLs are preserved as metadata. The schema does not claim OCR or extract text that appears only inside images, and analysis must not automatically follow links embedded in the article. X's article payload may omit trailing rich text or code blocks; a body ending with a colon receives a possible-truncation warning and must not be described as complete.

Before Codex analysis, `opportunities_path` contains a valid schema-version-2 placeholder with `analysis_input_hash`, `status: "awaiting_analysis"`, an empty `opportunities` list, and `recommended_execution: null`. After the requested analysis completes it preserves the same hash and contains `status: "analyzed"`. Each supported opportunity has a matching JSON item; `recommended_execution` mirrors an actual plan or stays null. Basic summaries and unsupported opportunities legitimately leave an empty list and null execution. If required method review is unavailable, retain `awaiting_analysis` rather than claiming the full requested analysis is complete.

The hash is a SHA-256 fingerprint of normalized analysis-relevant post and reply fields. A prepare run preserves analysis only when the previous and current hashes match. If the evidence changes, XBrief replaces the analysis with the waiting marker and resets `opportunities.json` to `awaiting_analysis`, preventing stale conclusions from appearing current.
