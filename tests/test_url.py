import pytest

from xbrief.errors import XBriefError
from xbrief.url import parse_tweet_url


@pytest.mark.parametrize(
    ("url", "tweet_id"),
    [
        ("https://x.com/alice/status/123", "123"),
        ("https://twitter.com/alice/status/456?s=20", "456"),
        ("https://mobile.twitter.com/alice/status/789/photo/1", "789"),
    ],
)
def test_parse_tweet_url(url: str, tweet_id: str) -> None:
    parsed = parse_tweet_url(url)
    assert parsed.tweet_id == tweet_id
    assert parsed.canonical_url == f"https://x.com/alice/status/{tweet_id}"


@pytest.mark.parametrize(
    "url",
    [
        "http://x.com/alice/status/123",
        "https://example.com/alice/status/123",
        "https://x.com/alice",
        "https://x.com/alice/status/not-a-number",
    ],
)
def test_reject_invalid_url(url: str) -> None:
    with pytest.raises(XBriefError, match="链接|接受"):
        parse_tweet_url(url)
