from xbrief.models import Reply
from xbrief.selector import select_replies


def _reply(index: int, **updates: object) -> Reply:
    payload = {
        "id": str(index),
        "root_tweet_id": "1",
        "parent_id": "1",
        "author_username": f"user{index}",
        "text": f"Detailed comment number {index} with useful information {index * 10}",
        "like_count": index,
        "repost_count": index // 2,
    }
    payload.update(updates)
    return Reply.model_validate(payload)


def test_selector_is_deterministic_and_bounded() -> None:
    replies = [_reply(index) for index in range(1, 40)]
    first = select_replies(replies, tweet_id="1", limit=24, char_budget=1600)
    second = select_replies(replies, tweet_id="1", limit=24, char_budget=1600)
    assert [item.reply.id for item in first] == [item.reply.id for item in second]
    assert len(first) <= 24
    assert sum(len(item.reply.text) for item in first) <= 1600
    assert len({item.reply.id for item in first}) == len(first)


def test_selector_removes_exact_normalized_duplicates() -> None:
    replies = [
        _reply(1, text="Same message", like_count=1),
        _reply(2, text="  same   message ", like_count=9),
    ]
    selected = select_replies(replies, tweet_id="1", limit=10, char_budget=1000)
    assert [item.reply.id for item in selected] == ["2"]
