from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from xbrief.errors import XBriefError
from xbrief.models import Post, ReplyPage
from xbrief.redaction import redact
from xbrief.security import cookie_file_safety
from xbrief.url import ParsedTweetUrl

ALLOWED_TOOLS = frozenset({"get_tweet", "get_tweet_replies"})
EXPECTED_TWIKIT_VERSION = "0.1.35"


class TwikitCliAdapter:
    source = "twikit"

    def __init__(
        self,
        *,
        binary: str,
        cookie_path: Path,
        timeout_seconds: int = 45,
        max_output_bytes: int = 5_000_000,
    ) -> None:
        self.binary = binary
        self.cookie_path = cookie_path
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def _resolved_binary(self) -> str:
        resolved = shutil.which(self.binary)
        if not resolved:
            raise XBriefError("config_error", f"找不到抓取器：{self.binary}")
        return resolved

    def _call(self, tool: str, **kwargs: str | None) -> dict[str, Any]:
        if tool not in ALLOWED_TOOLS:
            raise XBriefError("config_error", f"拒绝调用非只读工具：{tool}")
        cookie_ok, cookie_detail = cookie_file_safety(self.cookie_path)
        if not cookie_ok:
            raise XBriefError(
                "auth_failed", f"专用 X 账号 Cookie 未配置或权限不安全：{cookie_detail}。"
            )

        argv = [self._resolved_binary(), "call", tool]
        argv.extend(f"{key}={value}" for key, value in kwargs.items() if value is not None)
        env = {
            "HOME": str(Path.home()),
            "PATH": os.environ.get("PATH", ""),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "TWITTER_COOKIES": str(self.cookie_path),
        }
        if tmpdir := os.environ.get("TMPDIR"):
            env["TMPDIR"] = tmpdir

        try:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=False,
                timeout=self.timeout_seconds,
                env=env,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise XBriefError("backend_error", "X 抓取请求超时。", retryable=True) from exc

        stdout = completed.stdout or b""
        stderr = completed.stderr or b""
        if len(stdout) + len(stderr) > self.max_output_bytes:
            raise XBriefError("backend_error", "抓取器返回内容超过安全上限。")
        safe_stderr = redact(stderr.decode("utf-8", errors="replace"), self.cookie_path)
        if completed.returncode != 0:
            raise self._classify_error(safe_stderr)
        try:
            payload = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise XBriefError("backend_error", "抓取器没有返回有效 JSON。") from exc
        if not isinstance(payload, dict):
            raise XBriefError("backend_error", "抓取器返回了不支持的数据结构。")
        return payload

    @staticmethod
    def _classify_error(message: str) -> XBriefError:
        lowered = message.lower()
        if any(term in lowered for term in ("401", "unauthorized", "cookie", "auth")):
            return XBriefError("auth_failed", "X Cookie 无效或已经过期。")
        if any(term in lowered for term in ("not found", "404", "deleted")):
            return XBriefError("not_found", "帖子不存在或已经删除。")
        if any(term in lowered for term in ("private", "restricted", "forbidden", "403")):
            return XBriefError("restricted", "帖子为私密或当前账号不可访问。")
        if any(term in lowered for term in ("rate limit", "too many requests", "429")):
            return XBriefError("backend_error", "X 暂时限流。", retryable=True)
        return XBriefError("backend_error", "twikit-mcp 调用失败。", retryable=True)

    def fetch_post(self, parsed: ParsedTweetUrl) -> Post:
        data = self._call("get_tweet", tweet_id=parsed.tweet_id)
        try:
            return Post(
                id=str(data["id"]),
                canonical_url=parsed.canonical_url,
                conversation_id=_optional_str(data.get("conversation_id")),
                author_username=str(data.get("author") or parsed.username),
                author_display_name=_optional_str(data.get("author_name")),
                text=str(data.get("text") or ""),
                created_at=_optional_str(data.get("created_at")),
                like_count=_optional_int(data.get("likes")),
                repost_count=_optional_int(data.get("retweets")),
                quoted_id=_optional_str(data.get("quoted_id")),
                quoted_author=_optional_str(data.get("quoted_author")),
                quoted_text=_optional_str(data.get("quoted_text")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise XBriefError("backend_error", "原帖返回格式与固定契约不一致。") from exc

    def fetch_replies(self, parent_id: str, cursor: str | None = None) -> ReplyPage:
        data = self._call("get_tweet_replies", tweet_id=parent_id, cursor=cursor)
        raw_replies = data.get("replies") or []
        if not isinstance(raw_replies, list):
            raise XBriefError("backend_error", "评论页 replies 字段格式错误。")
        try:
            return ReplyPage(
                parent_id=parent_id,
                replies=[item for item in raw_replies if isinstance(item, dict)],
                next_cursor=_optional_str(data.get("next_cursor")),
                count=int(data.get("count") or len(raw_replies)),
            )
        except (TypeError, ValueError) as exc:
            raise XBriefError("backend_error", "评论页返回格式与固定契约不一致。") from exc


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
