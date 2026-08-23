from pathlib import Path

from xbrief.config import Settings
from xbrief.models import Post, ReplyPage
from xbrief.service import prepare
from xbrief.url import ParsedTweetUrl


class ServiceAdapter:
    source = "fake"

    def fetch_post(self, parsed: ParsedTweetUrl) -> Post:
        return Post(
            id=parsed.tweet_id,
            canonical_url=parsed.canonical_url,
            author_username="alice",
            text="A post",
        )

    def fetch_replies(self, parent_id: str, cursor: str | None = None) -> ReplyPage:
        if parent_id == "1":
            return ReplyPage(
                parent_id="1",
                replies=[{"id": "2", "author": "bob", "text": "A useful reply", "likes": 4}],
                count=1,
            )
        return ReplyPage(parent_id=parent_id, replies=[], count=0)


def test_prepare_end_to_end_with_fake_adapter(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(vault_path=vault, data_root=tmp_path / "data", max_depth=2)
    result = prepare(
        "https://x.com/alice/status/1",
        settings=settings,
        adapter=ServiceAdapter(),
        include_nested=True,
    )
    assert result.comments_fetched == 1
    assert Path(result.report_path).exists()
    assert Path(result.compact_context_path).exists()
    assert result.schema_version == 2
    assert Path(result.opportunities_path).exists()
    assert "A useful reply" in Path(result.comments_index_path).read_text(encoding="utf-8")
