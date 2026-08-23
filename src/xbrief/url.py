from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from xbrief.errors import XBriefError

_STATUS_RE = re.compile(r"^/([^/]+)/status/(\d+)(?:/.*)?$")
_ALLOWED_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}


@dataclass(frozen=True)
class ParsedTweetUrl:
    tweet_id: str
    username: str
    canonical_url: str


def parse_tweet_url(value: str) -> ParsedTweetUrl:
    raw = value.strip()
    if not raw:
        raise XBriefError("invalid_url", "X 帖子链接不能为空。")
    parsed = urlparse(raw)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise XBriefError("invalid_url", "只接受 https://x.com 或 https://twitter.com 帖子链接。")
    match = _STATUS_RE.match(parsed.path)
    if not match:
        raise XBriefError("invalid_url", "链接必须符合 /<user>/status/<数字ID> 格式。")
    username, tweet_id = match.groups()
    return ParsedTweetUrl(
        tweet_id=tweet_id,
        username=username,
        canonical_url=f"https://x.com/{username}/status/{tweet_id}",
    )
