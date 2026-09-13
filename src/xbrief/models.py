from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class Outcome(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class StopReason(StrEnum):
    CURSOR_EXHAUSTED = "cursor_exhausted"
    REPLY_CAP = "reply_cap"
    PAGE_CAP = "page_cap"
    RATE_LIMITED = "rate_limited"
    BACKEND_ERROR = "backend_error"
    AUTH_FAILED = "auth_failed"
    NOT_FOUND = "not_found"
    RESTRICTED = "restricted"
    INVALID_URL = "invalid_url"


class XArticle(BaseModel):
    id: str
    source_url: str
    title: str
    preview_text: str = ""
    plain_text: str
    cover_image: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    lifecycle_state: dict[str, Any] | None = None
    source: str = "twikit"


class Post(BaseModel):
    id: str
    canonical_url: str
    conversation_id: str | None = None
    author_username: str
    author_display_name: str | None = None
    text: str
    created_at: str | None = None
    like_count: int | None = None
    repost_count: int | None = None
    quoted_id: str | None = None
    quoted_author: str | None = None
    quoted_text: str | None = None
    article: XArticle | None = None
    article_warning: str | None = None
    source: str = "twikit"
    fetched_at: datetime = Field(default_factory=utc_now)


class Reply(BaseModel):
    id: str
    root_tweet_id: str
    parent_id: str
    depth: int = 1
    author_username: str
    author_display_name: str | None = None
    text: str
    created_at: str | None = None
    like_count: int | None = None
    repost_count: int | None = None
    is_author_reply: bool = False
    source_url: str | None = None
    source: str = "twikit"
    fetched_at: datetime = Field(default_factory=utc_now)


class ReplyPage(BaseModel):
    parent_id: str
    replies: list[dict[str, Any]]
    next_cursor: str | None = None
    count: int = 0


class FetchSummary(BaseModel):
    run_id: str
    tweet_id: str
    outcome: Outcome
    stop_reason: StopReason
    post_fetched: bool
    replies_fetched: int
    top_level_replies_fetched: int
    nested_replies_fetched: int
    pages_fetched: int
    pagination_completed: bool
    possible_missing_replies: bool = True
    remaining_cursor: str | None = None
    source: str = "twikit"
    warnings: list[str] = Field(default_factory=list)


class SelectedReply(BaseModel):
    reply: Reply
    selection_bucket: str
    selection_reasons: list[str]
    score: float
    rank: int


class PrepareResult(BaseModel):
    schema_version: int = 2
    run_id: str
    tweet_id: str
    outcome: Outcome
    stop_reason: StopReason
    comments_fetched: int
    compact_context_path: str
    analysis_prompt_path: str
    opportunities_path: str
    report_path: str
    comments_index_path: str
    warnings: list[str] = Field(default_factory=list)
