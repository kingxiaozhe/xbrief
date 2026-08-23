from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Iterable

from xbrief.models import Reply, SelectedReply

_URL_RE = re.compile(r"https?://\S+")
_SPACE_RE = re.compile(r"\s+")
_QUESTION_RE = re.compile(r"[?？]|\b(why|how|what|when|where|who)\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\d")


def select_replies(
    replies: Iterable[Reply], *, tweet_id: str, limit: int, char_budget: int
) -> list[SelectedReply]:
    candidates = _dedupe_and_filter(replies)
    seed = int(hashlib.sha256(f"{tweet_id}:selector-v1".encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    selected: list[tuple[Reply, str, list[str], float]] = []
    used: set[str] = set()

    def take(bucket: str, items: list[Reply], count: int, reason: str) -> None:
        for reply in items:
            if len([row for row in selected if row[1] == bucket]) >= count:
                break
            if reply.id in used:
                continue
            score = _score(reply)
            selected.append((reply, bucket, [reason], score))
            used.add(reply.id)

    take("author", [r for r in candidates if r.is_author_reply], 4, "原帖作者回复")
    take(
        "high_interaction",
        sorted(candidates, key=_engagement, reverse=True),
        6,
        "互动量较高",
    )
    take(
        "informative",
        sorted(candidates, key=_information_score, reverse=True),
        6,
        "信息量较高",
    )
    take("question", [r for r in candidates if _QUESTION_RE.search(r.text)], 2, "明确提问")

    low_interaction = sorted(candidates, key=_engagement)
    rng.shuffle(low_interaction)
    take("exploration", low_interaction, 4, "低互动探索样本")

    take("fill", sorted(candidates, key=_score, reverse=True), limit, "补足代表性样本")

    result: list[SelectedReply] = []
    consumed = 0
    for reply, bucket, reasons, score in selected:
        if len(result) >= limit:
            break
        size = len(reply.text)
        if result and consumed + size > char_budget:
            continue
        consumed += size
        result.append(
            SelectedReply(
                reply=reply,
                selection_bucket=bucket,
                selection_reasons=reasons,
                score=score,
                rank=len(result) + 1,
            )
        )
    return result


def _dedupe_and_filter(replies: Iterable[Reply]) -> list[Reply]:
    best: dict[str, Reply] = {}
    for reply in replies:
        normalized = _normalize(reply.text)
        if len(normalized) < 2 or not any(ch.isalnum() for ch in normalized):
            continue
        current = best.get(normalized)
        if current is None or _engagement(reply) > _engagement(current):
            best[normalized] = reply
    return list(best.values())


def _normalize(text: str) -> str:
    without_urls = _URL_RE.sub(" <url> ", text.casefold())
    return _SPACE_RE.sub(" ", without_urls).strip()


def _engagement(reply: Reply) -> int:
    return (reply.like_count or 0) + 2 * (reply.repost_count or 0)


def _information_score(reply: Reply) -> float:
    text = reply.text
    return (
        min(len(text), 400) / 20
        + 4 * len(_URL_RE.findall(text))
        + 2 * bool(_NUMBER_RE.search(text))
    )


def _score(reply: Reply) -> float:
    return _information_score(reply) + _engagement(reply) ** 0.5 + 3 * reply.is_author_reply
