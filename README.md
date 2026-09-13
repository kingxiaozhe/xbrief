# XBrief

XBrief is an open-source Codex Skill and local Python CLI for archiving one X post and the replies visible to your account in Obsidian, then producing an evidence-bounded Chinese analysis from that saved material.

It stores the full captured discussion separately from the compact context used for analysis, so source text, comments, facts, opinions, and model inference remain distinguishable.

## What it does

- Accepts one canonical X or Twitter status URL.
- Fetches the post and visible top-level and nested replies through a fixed read-only twikit-mcp adapter.
- When the post embeds an X Article, captures its title, plain-text body, cover, and media URLs through the same read-only adapter.
- Saves the complete capture in an Obsidian-friendly folder structure.
- Creates a compact analysis context and a report template with coverage warnings.
- Uses the bundled evidence-first method panel for business opportunities, material effort/cost decisions, execution plans, or an explicit method-review request; basic summaries need source checks only.
- Preserves the limits of account visibility, deleted or hidden replies, pagination caps, and unverified claims.

## Install

Prerequisites:

- Python 3.11 or newer;
- uv;
- the compatible twikit-mcp CLI, currently pinned to 0.1.35;
- an Obsidian Vault you are allowed to write to;
- a dedicated X account configured locally for the underlying client. Keep its authentication material out of chat, Git, logs, and screenshots.

~~~bash
git clone https://github.com/kingxiaozhe/xbrief.git
cd xbrief
uv sync --all-groups
uv run xbrief configure --vault /absolute/path/to/your/ObsidianVault
uv run xbrief doctor --json
~~~

The CLI has no fallback Vault path. Until configuration is complete, it stops safely instead of writing to an implicit local directory. XBRIEF_VAULT can provide a temporary Vault path for automation.

## Use in Codex

Install skills/xbrief and skills/nuwa-business-panel into the directories your Codex installation discovers, then start a task with:

~~~text
Use $xbrief to archive and analyze:
https://x.com/<user>/status/<id>
~~~

The Skill now defaults to read-only analysis in the Codex built-in browser. “看看右侧帖子有什么用” or “用 $xbrief 分析，不保存” does not run the archive CLI or write to the Vault. A referenced browser tab can supply the single status URL.

Only an explicit save/archive request selects archival mode, which invokes xbrief doctor --json before fetching. It preserves the archive even when analysis cannot proceed, and stops rather than claiming that comments or external facts were fully verified. The CLI's persistence boundary is unchanged: `prepare` always writes an archive and is not a read-only fetch command.

Both modes require evidence-bounded source checks. Method review is required for business opportunities, material effort/cost decisions, execution plans or an explicit review request; saving alone does not activate it. A missing panel blocks only dependent conclusions, not an independently supported summary. Sparse comments are not padded to meet a quota; a post without credible demand evidence does not receive an invented business plan. Read-only answers are compact and labeled 未归档; archival reports retain the nine-section format.

## CLI

~~~bash
uv run xbrief doctor --json
uv run xbrief prepare --json "https://x.com/<user>/status/<id>"
uv run xbrief prepare --json --top-level-only "https://x.com/<user>/status/<id>"
~~~

Default safety limits are 250 pages, 1,000 replies, and nested depth 3. Hitting a cap returns partial; already captured replies remain available in the Vault.

## Obsidian output

~~~text
XBrief/YYYY/MM/<tweet_id>/
├── index.md
├── comments.md
├── comments-002.md
└── _data/
    ├── post.json
    ├── article.json          # only when the post embeds a readable X Article
    ├── replies.jsonl
    ├── fetch-meta.json
    ├── compact-context.json
    ├── analysis-prompt.md
    └── opportunities.json
~~~

Comments and JSONL files retain the full fetched reply set. The compact context is only the representative sample supplied to the analysis task; when present, the X Article body is included as author-source evidence. Opportunity cards use the repository's E0–E5 evidence ladder and must not treat engagement as proof of demand.

## Security and limits

XBrief permits only four fixed read-only backend calls: get_tweet, get_tweet_replies, get_article_preview, and get_article. It rejects unsafe cookie-file permissions and symlinks, redacts authentication-like values from backend errors, and never accepts arbitrary backend tool calls.

Article capture does not follow links embedded in the article. Media URLs are archived, but text shown only inside images is not treated as extracted article text. X's article payload can also omit trailing rich text or code blocks; when the returned body ends with a colon, XBrief emits a visible possible-truncation warning instead of calling it complete.

X visibility is not completeness: a finished cursor only describes what the current account and backend exposed at that time. Hidden, deleted, collapsed, restricted, or differently ranked replies may be absent.

## Development

~~~bash
uv run ruff check src tests
uv run pytest
~~~

## License

[MIT](LICENSE) © 2026 kingxiaozhe
