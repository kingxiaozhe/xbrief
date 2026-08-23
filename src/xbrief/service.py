from __future__ import annotations

from collections import Counter
from typing import Any

from xbrief.adapters.base import FetchAdapter
from xbrief.adapters.twikit_cli import TwikitCliAdapter
from xbrief.config import Settings
from xbrief.models import Post, PrepareResult, Reply, SelectedReply
from xbrief.obsidian import write_obsidian_bundle
from xbrief.paginator import fetch_reply_tree
from xbrief.selector import select_replies
from xbrief.storage import Storage
from xbrief.url import parse_tweet_url


def prepare(
    url: str,
    *,
    settings: Settings,
    adapter: FetchAdapter | None = None,
    include_nested: bool | None = None,
) -> PrepareResult:
    parsed = parse_tweet_url(url)
    settings.require_vault()
    storage = Storage(settings.database_path)
    active_adapter = adapter or TwikitCliAdapter(
        binary=settings.twikit_binary,
        cookie_path=settings.cookie_path,
        timeout_seconds=settings.subprocess_timeout_seconds,
    )
    post = active_adapter.fetch_post(parsed)
    storage.save_post(post)
    run_id = storage.create_run(post.id)
    summary = fetch_reply_tree(
        adapter=active_adapter,
        storage=storage,
        run_id=run_id,
        tweet_id=post.id,
        post_author=post.author_username,
        include_nested=settings.include_nested if include_nested is None else include_nested,
        max_depth=settings.max_depth,
        max_pages=settings.max_pages,
        max_replies=settings.max_replies,
    )
    replies = storage.replies_for_tweet(post.id)
    summary = summary.model_copy(
        update={
            "replies_fetched": len(replies),
            "top_level_replies_fetched": sum(reply.depth == 1 for reply in replies),
            "nested_replies_fetched": sum(reply.depth > 1 for reply in replies),
        }
    )
    storage.finish_run(summary)
    selected = select_replies(
        replies,
        tweet_id=post.id,
        limit=settings.max_comments_for_model,
        char_budget=settings.max_model_input_chars,
    )
    compact = _compact_context(post, replies, selected, summary.model_dump(mode="json"))
    paths = write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=replies,
        summary=summary,
        compact_context=compact,
    )
    return PrepareResult(
        run_id=run_id,
        tweet_id=post.id,
        outcome=summary.outcome,
        stop_reason=summary.stop_reason,
        comments_fetched=summary.replies_fetched,
        compact_context_path=str(paths["compact_context"].resolve()),
        analysis_prompt_path=str(paths["analysis_prompt"].resolve()),
        opportunities_path=str(paths["opportunities"].resolve()),
        report_path=str(paths["report"].resolve()),
        comments_index_path=str(paths["comments_index"].resolve()),
        warnings=summary.warnings,
    )


def _compact_context(
    post: Post,
    replies: list[Reply],
    selected: list[SelectedReply],
    fetch_meta: dict[str, Any],
) -> dict[str, Any]:
    buckets = Counter(item.selection_bucket for item in selected)
    return {
        "schema_version": 1,
        "post": post.model_dump(mode="json"),
        "fetch_meta": fetch_meta,
        "basic_stats": {
            "total_saved": len(replies),
            "unique_authors": len({reply.author_username.casefold() for reply in replies}),
            "author_replies": sum(reply.is_author_reply for reply in replies),
            "nested_replies": sum(reply.depth > 1 for reply in replies),
        },
        "selection": {
            "selector_version": "v1",
            "selected": len(selected),
            "bucket_counts": dict(buckets),
        },
        "representative_comments": [item.model_dump(mode="json") for item in selected],
        "warnings": fetch_meta.get("warnings", []),
    }
