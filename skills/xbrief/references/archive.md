# Archive workflow

Only execute after explicit save/archive intent. The local CLI writes to the configured Vault; never use this branch merely to read.

1. Accept exactly one X or Twitter status URL. If missing, resolve the referenced built-in browser tab or request it.
2. Run `xbrief doctor --json`. If required capture dependencies are unavailable, report it and stop capture. A panel-only failure is not a capture failure: the current doctor may still report overall failure for it; proceed only if every capture check passes and the failure is isolated to the panel. Never bypass credential, backend or Vault failures.
3. Run `xbrief prepare --json <url>`. Never construct backend calls or inspect browser credentials.
4. Do not analyze comments after failure. For partial results preserve the coverage warning.
5. Read returned compact context and analysis prompt. When an X Article is present, treat its plain-text body as author-source evidence, not independently verified fact. Do not load the full reply archive unless the user requests exhaustive review or identifies a specific comment.
6. Read [report format](report-format.md) and [output schema](output-schema.md). Saving alone does not require commercial analysis. Apply SKILL.md's depth gate and sparse-comment rules even if the generated prompt mandates a panel or business plan. When depth requires it, use [panel adapter](expert-panel.md); if unavailable preserve capture and return only independently supported facts labeled 未完成方法审查.
7. Replace only the report's analysis markers. Write matching JSON only to the returned opportunities path. Re-read both outputs to check consistency, evidence links, hashes, empty-opportunity handling and coverage warnings.

The CLI permits only fixed read-only post, reply, article-preview and article backend calls. Cursor exhaustion describes account visibility, never complete X coverage. Archival media URLs do not prove OCR or video transcription.

If requested method review is blocked, do not mark the requested full analysis complete: preserve awaiting_analysis JSON/status and report the incomplete portion. Do not silently replace a prior full analysis with a lower-depth version on a same-evidence rerun; explain and ask only if that overwrite is required.
