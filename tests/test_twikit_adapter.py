from __future__ import annotations

import os
from pathlib import Path

import pytest

from xbrief.adapters.twikit_cli import TwikitCliAdapter
from xbrief.errors import XBriefError
from xbrief.url import parse_tweet_url

FAKE_BINARY = r"""#!/usr/bin/env python3
import json
import sys

tool = sys.argv[2]
args = dict(item.split("=", 1) for item in sys.argv[3:])
if tool == "get_tweet":
    print(json.dumps({
        "id": args["tweet_id"],
        "author": "alice",
        "author_name": "Alice",
        "text": "hello",
        "created_at": "now",
        "likes": 3,
        "retweets": 1,
        "conversation_id": args["tweet_id"],
    }))
elif tool == "get_tweet_replies":
    print(json.dumps({
        "tweet_id": args["tweet_id"],
        "replies": [{"id": "2", "author": "bob", "text": "reply", "likes": 1}],
        "next_cursor": "next" if "cursor" not in args else None,
        "count": 1,
    }))
else:
    print("bad", file=sys.stderr)
    raise SystemExit(2)
"""

ARTICLE_FAKE_BINARY = r"""#!/usr/bin/env python3
import json
import sys

tool = sys.argv[2]
args = dict(item.split("=", 1) for item in sys.argv[3:])
if tool == "get_tweet":
    print(json.dumps({
        "id": args["tweet_id"],
        "author": "alice",
        "text": "https://t.co/article",
        "conversation_id": args["tweet_id"],
    }))
elif tool == "get_article_preview":
    print(json.dumps({
        "rest_id": "article-9",
        "title": "A useful workflow",
        "preview_text": "preview",
        "cover_image": "https://pbs.twimg.com/cover.jpg",
        "tweet_id": args["tweet_id"],
        "author": "alice",
    }))
elif tool == "get_article":
    print(json.dumps({
        "rest_id": args["article_id"],
        "title": "A useful workflow",
        "preview_text": "preview",
        "plain_text": "full article body",
        "cover_image": "https://pbs.twimg.com/cover.jpg",
        "media": ["https://pbs.twimg.com/one.png"],
        "lifecycle_state": {"modified_at_secs": 123},
    }))
elif tool == "get_tweet_replies":
    print(json.dumps({"tweet_id": args["tweet_id"], "replies": [], "count": 0}))
else:
    print("bad", file=sys.stderr)
    raise SystemExit(2)
"""


def _adapter(tmp_path: Path) -> TwikitCliAdapter:
    binary = tmp_path / "twikit-mcp"
    binary.write_text(FAKE_BINARY, encoding="utf-8")
    os.chmod(binary, 0o755)
    cookie = tmp_path / "cookies.json"
    cookie.write_text("{}", encoding="utf-8")
    os.chmod(cookie, 0o600)
    return TwikitCliAdapter(binary=str(binary), cookie_path=cookie)


def _adapter_with_binary(tmp_path: Path, source: str) -> TwikitCliAdapter:
    binary = tmp_path / "twikit-mcp"
    binary.write_text(source, encoding="utf-8")
    os.chmod(binary, 0o755)
    cookie = tmp_path / "cookies.json"
    cookie.write_text("{}", encoding="utf-8")
    os.chmod(cookie, 0o600)
    return TwikitCliAdapter(binary=str(binary), cookie_path=cookie)


def test_fetch_post_and_replies(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    post = adapter.fetch_post(parse_tweet_url("https://x.com/alice/status/1"))
    page = adapter.fetch_replies("1")
    assert post.id == "1"
    assert post.author_username == "alice"
    assert page.next_cursor == "next"
    assert page.replies[0]["id"] == "2"


def test_fetch_post_enriches_tco_article_with_fixed_readonly_tools(tmp_path: Path) -> None:
    adapter = _adapter_with_binary(tmp_path, ARTICLE_FAKE_BINARY)

    post = adapter.fetch_post(parse_tweet_url("https://x.com/alice/status/1"))

    assert post.article is not None
    assert post.article.id == "article-9"
    assert post.article.source_url == "https://x.com/i/article/article-9"
    assert post.article.title == "A useful workflow"
    assert post.article.plain_text == "full article body"
    assert post.article.media_urls == ["https://pbs.twimg.com/one.png"]
    assert post.article_warning is None


def test_non_article_tco_keeps_post_with_visible_warning(tmp_path: Path) -> None:
    source = ARTICLE_FAKE_BINARY.replace(
        'print(json.dumps({\n        "rest_id": "article-9",',
        'print("Tweet 1 does not embed an article.", file=sys.stderr)\n'
        "    raise SystemExit(2)\n"
        '    print(json.dumps({\n        "rest_id": "article-9",',
    )
    adapter = _adapter_with_binary(tmp_path, source)

    post = adapter.fetch_post(parse_tweet_url("https://x.com/alice/status/1"))

    assert post.article is None
    assert post.article_warning == "检测到短链接，但它不是可读取的 X Article。"


def test_article_ending_with_colon_has_possible_truncation_warning(
    tmp_path: Path,
) -> None:
    source = ARTICLE_FAKE_BINARY.replace(
        '"plain_text": "full article body",',
        '"plain_text": "code follows：",',
    )
    adapter = _adapter_with_binary(tmp_path, source)

    post = adapter.fetch_post(parse_tweet_url("https://x.com/alice/status/1"))

    assert post.article is not None
    assert post.article_warning == (
        "X Article 正文以冒号结尾；上游可能未返回后续富文本或代码块，请核对页面。"
    )


def test_refuses_non_readonly_tool(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    with pytest.raises(XBriefError, match="非只读"):
        adapter._call("send_tweet", text="no")  # noqa: SLF001


def test_missing_cookie_is_auth_failure(tmp_path: Path) -> None:
    adapter = TwikitCliAdapter(binary="true", cookie_path=tmp_path / "missing.json")
    with pytest.raises(XBriefError) as exc:
        adapter.fetch_replies("1")
    assert exc.value.code == "auth_failed"


def test_unsafe_cookie_permissions_are_rejected(tmp_path: Path) -> None:
    binary = tmp_path / "twikit-mcp"
    binary.write_text(FAKE_BINARY, encoding="utf-8")
    os.chmod(binary, 0o755)
    cookie = tmp_path / "cookies.json"
    cookie.write_text("{}", encoding="utf-8")
    os.chmod(cookie, 0o644)
    adapter = TwikitCliAdapter(binary=str(binary), cookie_path=cookie)
    with pytest.raises(XBriefError, match="权限不安全"):
        adapter.fetch_replies("1")


def test_contract_drift_is_structured_backend_error(tmp_path: Path) -> None:
    binary = tmp_path / "twikit-mcp"
    binary.write_text("#!/usr/bin/env python3\nprint('{}')\n", encoding="utf-8")
    os.chmod(binary, 0o755)
    cookie = tmp_path / "cookies.json"
    cookie.write_text("{}", encoding="utf-8")
    os.chmod(cookie, 0o600)
    adapter = TwikitCliAdapter(binary=str(binary), cookie_path=cookie)
    with pytest.raises(XBriefError) as exc:
        adapter.fetch_post(parse_tweet_url("https://x.com/alice/status/1"))
    assert exc.value.code == "backend_error"
