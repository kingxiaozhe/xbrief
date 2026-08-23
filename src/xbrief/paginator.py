from __future__ import annotations

from collections import deque

from xbrief.adapters.base import FetchAdapter
from xbrief.errors import XBriefError
from xbrief.models import FetchSummary, Outcome, Reply, StopReason
from xbrief.storage import Storage


def fetch_reply_tree(
    *,
    adapter: FetchAdapter,
    storage: Storage,
    run_id: str,
    tweet_id: str,
    post_author: str,
    include_nested: bool,
    max_depth: int,
    max_pages: int,
    max_replies: int,
) -> FetchSummary:
    queue: deque[tuple[str, int]] = deque([(tweet_id, 0)])
    queued_parents = {tweet_id}
    seen_reply_ids: set[str] = set()
    pages_fetched = 0
    top_level = 0
    nested = 0
    outcome = Outcome.SUCCESS
    stop_reason = StopReason.CURSOR_EXHAUSTED
    remaining_cursor: str | None = None
    warnings: list[str] = []
    interrupted = False

    while queue and not interrupted:
        parent_id, parent_depth = queue.popleft()
        cursor: str | None = None
        seen_cursors: set[str] = set()
        while True:
            if max_pages and pages_fetched >= max_pages:
                outcome = Outcome.PARTIAL
                stop_reason = StopReason.PAGE_CAP
                warnings.append(f"达到安全页数上限 {max_pages}。")
                interrupted = True
                break
            if max_replies and len(seen_reply_ids) >= max_replies:
                outcome = Outcome.PARTIAL
                stop_reason = StopReason.REPLY_CAP
                warnings.append(f"达到安全评论上限 {max_replies}。")
                interrupted = True
                break
            try:
                page = adapter.fetch_replies(parent_id, cursor)
            except XBriefError as exc:
                outcome = Outcome.FAILURE if pages_fetched == 0 else Outcome.PARTIAL
                stop_reason = _stop_reason_for(exc)
                warnings.append(exc.message)
                remaining_cursor = cursor
                interrupted = True
                break

            pages_fetched += 1
            normalized: list[Reply] = []
            for raw in page.replies:
                reply_id = str(raw.get("id") or "")
                if not reply_id or reply_id in {tweet_id, parent_id}:
                    continue
                if reply_id in seen_reply_ids:
                    continue
                if max_replies and len(seen_reply_ids) + len(normalized) >= max_replies:
                    outcome = Outcome.PARTIAL
                    stop_reason = StopReason.REPLY_CAP
                    warnings.append(f"达到安全评论上限 {max_replies}。")
                    interrupted = True
                    break
                depth = parent_depth + 1
                author = str(raw.get("author") or "unknown")
                normalized.append(
                    Reply(
                        id=reply_id,
                        root_tweet_id=tweet_id,
                        parent_id=parent_id,
                        depth=depth,
                        author_username=author,
                        text=str(raw.get("text") or ""),
                        created_at=_optional_str(raw.get("created_at")),
                        like_count=_optional_int(raw.get("likes")),
                        repost_count=_optional_int(raw.get("retweets")),
                        is_author_reply=author.casefold() == post_author.casefold(),
                        source_url=f"https://x.com/{author}/status/{reply_id}",
                    )
                )

            storage.commit_page(
                run_id=run_id,
                parent_id=parent_id,
                cursor_in=cursor,
                cursor_out=page.next_cursor,
                page_index=pages_fetched,
                raw_count=page.count,
                replies=normalized,
            )
            for reply in normalized:
                seen_reply_ids.add(reply.id)
                if reply.depth == 1:
                    top_level += 1
                else:
                    nested += 1
                if include_nested and reply.depth < max_depth and reply.id not in queued_parents:
                    queue.append((reply.id, reply.depth))
                    queued_parents.add(reply.id)

            if interrupted:
                remaining_cursor = page.next_cursor
                break
            next_cursor = page.next_cursor
            if not next_cursor:
                break
            if next_cursor == cursor or next_cursor in seen_cursors:
                outcome = Outcome.PARTIAL
                stop_reason = StopReason.BACKEND_ERROR
                warnings.append("上游返回重复游标，已停止以避免死循环。")
                remaining_cursor = next_cursor
                interrupted = True
                break
            if cursor:
                seen_cursors.add(cursor)
            cursor = next_cursor

    if not include_nested and outcome is Outcome.SUCCESS:
        warnings.append("当前运行只抓取顶层评论，未展开嵌套回复。")

    summary = FetchSummary(
        run_id=run_id,
        tweet_id=tweet_id,
        outcome=outcome,
        stop_reason=stop_reason,
        post_fetched=True,
        replies_fetched=len(seen_reply_ids),
        top_level_replies_fetched=top_level,
        nested_replies_fetched=nested,
        pages_fetched=pages_fetched,
        pagination_completed=not interrupted and not queue,
        possible_missing_replies=True,
        remaining_cursor=remaining_cursor,
        warnings=warnings,
    )
    storage.finish_run(summary)
    return summary


def _stop_reason_for(error: XBriefError) -> StopReason:
    return {
        "auth_failed": StopReason.AUTH_FAILED,
        "not_found": StopReason.NOT_FOUND,
        "restricted": StopReason.RESTRICTED,
    }.get(error.code, StopReason.RATE_LIMITED if error.retryable else StopReason.BACKEND_ERROR)


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
