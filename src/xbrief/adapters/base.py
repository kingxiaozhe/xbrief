from __future__ import annotations

from typing import Protocol

from xbrief.models import Post, ReplyPage
from xbrief.url import ParsedTweetUrl


class FetchAdapter(Protocol):
    source: str

    def fetch_post(self, parsed: ParsedTweetUrl) -> Post: ...

    def fetch_replies(self, parent_id: str, cursor: str | None = None) -> ReplyPage: ...
