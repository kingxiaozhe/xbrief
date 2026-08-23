from __future__ import annotations

from pathlib import Path

from xbrief.errors import XBriefError
from xbrief.models import Post, Reply, ReplyPage
from xbrief.paginator import fetch_reply_tree
from xbrief.storage import Storage
from xbrief.url import ParsedTweetUrl


class FakeAdapter:
    source = "fake"

    def fetch_post(self, parsed: ParsedTweetUrl) -> Post:
        raise NotImplementedError

    def fetch_replies(self, parent_id: str, cursor: str | None = None) -> ReplyPage:
        if parent_id == "1" and cursor is None:
            return ReplyPage(
                parent_id="1",
                replies=[
                    {"id": "2", "author": "bob", "text": "first", "likes": 3},
                    {"id": "3", "author": "alice", "text": "author reply", "likes": 2},
                ],
                next_cursor="c2",
                count=2,
            )
        if parent_id == "1" and cursor == "c2":
            return ReplyPage(
                parent_id="1",
                replies=[
                    {"id": "3", "author": "alice", "text": "author reply", "likes": 2},
                    {"id": "4", "author": "carol", "text": "second page", "likes": 1},
                ],
                count=2,
            )
        if parent_id == "2":
            return ReplyPage(
                parent_id="2",
                replies=[{"id": "5", "author": "dan", "text": "nested", "likes": 0}],
                count=1,
            )
        return ReplyPage(parent_id=parent_id, replies=[], count=0)


def test_pagination_dedupes_and_fetches_nested(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    run_id = storage.create_run("1")
    summary = fetch_reply_tree(
        adapter=FakeAdapter(),
        storage=storage,
        run_id=run_id,
        tweet_id="1",
        post_author="alice",
        include_nested=True,
        max_depth=2,
        max_pages=20,
        max_replies=100,
    )
    replies = storage.replies_for_run(run_id)
    assert {reply.id for reply in replies} == {"2", "3", "4", "5"}
    assert summary.replies_fetched == 4
    assert summary.top_level_replies_fetched == 3
    assert summary.nested_replies_fetched == 1
    assert summary.pagination_completed is True
    assert next(reply for reply in replies if reply.id == "3").is_author_reply is True


def test_reply_cap_marks_partial(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    run_id = storage.create_run("1")
    summary = fetch_reply_tree(
        adapter=FakeAdapter(),
        storage=storage,
        run_id=run_id,
        tweet_id="1",
        post_author="alice",
        include_nested=True,
        max_depth=3,
        max_pages=20,
        max_replies=2,
    )
    assert summary.outcome.value == "partial"
    assert summary.stop_reason.value == "reply_cap"
    assert len(storage.replies_for_run(run_id)) == 2


class RepeatingCursorAdapter(FakeAdapter):
    def fetch_replies(self, parent_id: str, cursor: str | None = None) -> ReplyPage:
        return ReplyPage(
            parent_id=parent_id,
            replies=[{"id": "2", "author": "bob", "text": "one"}],
            next_cursor="loop",
            count=1,
        )


def test_repeating_cursor_stops_without_looping(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    run_id = storage.create_run("1")
    summary = fetch_reply_tree(
        adapter=RepeatingCursorAdapter(),
        storage=storage,
        run_id=run_id,
        tweet_id="1",
        post_author="alice",
        include_nested=False,
        max_depth=1,
        max_pages=20,
        max_replies=100,
    )
    assert summary.outcome.value == "partial"
    assert summary.stop_reason.value == "backend_error"
    assert summary.pages_fetched == 2


class PartialFailureAdapter(FakeAdapter):
    def fetch_replies(self, parent_id: str, cursor: str | None = None) -> ReplyPage:
        if cursor is None:
            return ReplyPage(
                parent_id=parent_id,
                replies=[{"id": "2", "author": "bob", "text": "saved"}],
                next_cursor="next",
                count=1,
            )
        raise XBriefError("backend_error", "limited", retryable=True)


def test_partial_failure_preserves_committed_page(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    run_id = storage.create_run("1")
    summary = fetch_reply_tree(
        adapter=PartialFailureAdapter(),
        storage=storage,
        run_id=run_id,
        tweet_id="1",
        post_author="alice",
        include_nested=False,
        max_depth=1,
        max_pages=20,
        max_replies=100,
    )
    assert summary.outcome.value == "partial"
    assert [reply.id for reply in storage.replies_for_run(run_id)] == ["2"]


def test_tweet_archive_keeps_replies_across_runs(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "test.sqlite3")
    for reply_id in ("2", "3"):
        run_id = storage.create_run("1")
        storage.commit_page(
            run_id=run_id,
            parent_id="1",
            cursor_in=None,
            cursor_out=None,
            page_index=1,
            raw_count=1,
            replies=[
                Reply(
                    id=reply_id,
                    root_tweet_id="1",
                    parent_id="1",
                    author_username="user",
                    text=f"reply {reply_id}",
                )
            ],
        )
    assert [reply.id for reply in storage.replies_for_tweet("1")] == ["2", "3"]
