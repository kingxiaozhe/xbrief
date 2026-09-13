import json
from pathlib import Path

from xbrief.config import Settings
from xbrief.models import FetchSummary, Outcome, Post, Reply, StopReason
from xbrief.obsidian import (
    ANALYSIS_END,
    ANALYSIS_START,
    _render_analysis_prompt,
    write_obsidian_bundle,
)


def test_generated_prompt_matches_optional_depth_and_sparse_comments(tmp_path: Path) -> None:
    post = Post(
        id="1", canonical_url="https://x.com/alice/status/1",
        author_username="alice", text="post",
    )
    summary = FetchSummary(
        run_id="run", tweet_id="1", outcome=Outcome.SUCCESS,
        stop_reason=StopReason.CURSOR_EXHAUSTED,
        post_fetched=True, replies_fetched=0, top_level_replies_fetched=0,
        nested_replies_fetched=0, pages_fetched=1, pagination_completed=True,
    )
    prompt = _render_analysis_prompt(
        post, summary, tmp_path / "context.json", tmp_path / "index.md",
        tmp_path / "opportunities.json",
    )
    assert "保存本身不要求商业分析" in prompt
    assert "选择 0–6 条" in prompt
    assert "不适用（本次仅摘要）" in prompt
    assert "未完成方法审查" in prompt
    assert "recommended_execution 为 null" in prompt
    assert "awaiting_analysis" in prompt
    assert "必须运行 $nuwa-business-panel" not in prompt


def test_writes_full_obsidian_bundle_and_preserves_analysis(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(
        vault_path=vault,
        data_root=tmp_path / "data",
        comments_per_note=1,
    )
    post = Post(
        id="1",
        canonical_url="https://x.com/alice/status/1",
        author_username="alice",
        text="post body",
    )
    replies = [
        Reply(
            id=str(index),
            root_tweet_id="1",
            parent_id="1",
            author_username=f"user{index}",
            text=f"comment {index}",
        )
        for index in (2, 3)
    ]
    summary = FetchSummary(
        run_id="run",
        tweet_id="1",
        outcome=Outcome.SUCCESS,
        stop_reason=StopReason.CURSOR_EXHAUSTED,
        post_fetched=True,
        replies_fetched=2,
        top_level_replies_fetched=2,
        nested_replies_fetched=0,
        pages_fetched=1,
        pagination_completed=True,
    )
    paths = write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=replies,
        summary=summary,
        compact_context={"representative_comments": []},
    )
    assert paths["report"].exists()
    assert paths["replies"].read_text(encoding="utf-8").count("\n") == 2
    assert (paths["report"].parent / "comments-002.md").exists()

    opportunities = paths["opportunities"].read_text(encoding="utf-8")
    assert '"schema_version": 2' in opportunities
    assert '"status": "awaiting_analysis"' in opportunities
    assert '"opportunities": []' in opportunities
    assert '"recommended_execution": null' in opportunities
    placeholder = json.loads(opportunities)
    assert len(placeholder["analysis_input_hash"]) == 64

    prompt = paths["analysis_prompt"].read_text(encoding="utf-8")
    assert "一句话说清楚" in prompt
    assert "最核心评论（原文 + 解读）" in prompt
    assert "赚钱机会与产品启发" in prompt
    assert "专家方法审查" in prompt
    assert "$nuwa-business-panel" in prompt
    assert "保留归档、暂停依赖它的结论" in prompt
    assert "不能输出完整或部分面板结论" in prompt
    assert "普通提问或索取免费建议不算 E3" in prompt
    assert "入选评论中的重复主题" in prompt
    assert "Nuwa fidelity" in prompt
    assert placeholder["analysis_input_hash"] in prompt
    assert "如果建议你落地：执行方案" in prompt
    assert "继续、调整和停止标准" in prompt
    assert "E0–E5" in prompt
    assert str(paths["opportunities"]) in prompt

    report = paths["report"].read_text(encoding="utf-8")
    report = report.replace(
        f"{ANALYSIS_START}\n_等待当前 Codex 根据 compact context 生成分析。_\n{ANALYSIS_END}",
        f"{ANALYSIS_START}\n我的分析\n{ANALYSIS_END}",
    )
    paths["report"].write_text(report, encoding="utf-8")
    write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=replies,
        summary=summary,
        compact_context={"representative_comments": []},
    )
    assert "我的分析" in paths["report"].read_text(encoding="utf-8")
    assert '"status": "awaiting_analysis"' in paths["opportunities"].read_text(
        encoding="utf-8"
    )


def test_changed_evidence_invalidates_preserved_analysis(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(vault_path=vault, data_root=tmp_path / "data")
    post = Post(
        id="1",
        canonical_url="https://x.com/alice/status/1",
        author_username="alice",
        text="post body",
    )
    reply = Reply(
        id="2",
        root_tweet_id="1",
        parent_id="1",
        author_username="bob",
        text="first evidence",
    )
    summary = FetchSummary(
        run_id="run-1",
        tweet_id="1",
        outcome=Outcome.SUCCESS,
        stop_reason=StopReason.CURSOR_EXHAUSTED,
        post_fetched=True,
        replies_fetched=1,
        top_level_replies_fetched=1,
        nested_replies_fetched=0,
        pages_fetched=1,
        pagination_completed=True,
    )
    paths = write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=[reply],
        summary=summary,
        compact_context={"representative_comments": []},
    )
    original = json.loads(paths["opportunities"].read_text(encoding="utf-8"))
    original["status"] = "analyzed"
    original["opportunities"] = [{"title": "old"}]
    paths["opportunities"].write_text(
        json.dumps(original, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = paths["report"].read_text(encoding="utf-8").replace(
        "_等待当前 Codex 根据 compact context 生成分析。_",
        "旧分析",
    )
    paths["report"].write_text(report, encoding="utf-8")

    changed_reply = reply.model_copy(update={"text": "changed evidence"})
    write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=[changed_reply],
        summary=summary.model_copy(update={"run_id": "run-2"}),
        compact_context={"representative_comments": []},
    )

    changed = json.loads(paths["opportunities"].read_text(encoding="utf-8"))
    assert changed["status"] == "awaiting_analysis"
    assert changed["opportunities"] == []
    assert changed["analysis_input_hash"] != original["analysis_input_hash"]
    refreshed_report = paths["report"].read_text(encoding="utf-8")
    assert "旧分析" not in refreshed_report
    assert "等待当前 Codex" in refreshed_report


def test_article_is_archived_rendered_and_invalidates_analysis(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(vault_path=vault, data_root=tmp_path / "data")
    article = {
        "id": "article-9",
        "source_url": "https://x.com/i/article/article-9",
        "title": "A useful workflow",
        "preview_text": "preview",
        "plain_text": "first article body",
        "cover_image": "https://pbs.twimg.com/cover.jpg",
        "media_urls": ["https://pbs.twimg.com/one.png"],
        "lifecycle_state": {"modified_at_secs": 123},
    }
    post = Post.model_validate(
        {
            "id": "1",
            "canonical_url": "https://x.com/alice/status/1",
            "author_username": "alice",
            "text": "https://t.co/article",
            "article": article,
        }
    )
    summary = FetchSummary(
        run_id="run-1",
        tweet_id="1",
        outcome=Outcome.SUCCESS,
        stop_reason=StopReason.CURSOR_EXHAUSTED,
        post_fetched=True,
        replies_fetched=0,
        top_level_replies_fetched=0,
        nested_replies_fetched=0,
        pages_fetched=1,
        pagination_completed=True,
    )

    paths = write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=[],
        summary=summary,
        compact_context={"post": post.model_dump(mode="json")},
    )

    assert paths["article"].exists()
    article_payload = json.loads(paths["article"].read_text(encoding="utf-8"))
    assert article_payload["plain_text"] == "first article body"
    report = paths["report"].read_text(encoding="utf-8")
    assert "## X Article" in report
    assert "A useful workflow" in report
    assert "first article body" in report
    prompt = paths["analysis_prompt"].read_text(encoding="utf-8")
    assert "X Article 正文属于作者来源文本" in prompt

    original_hash = json.loads(
        paths["opportunities"].read_text(encoding="utf-8")
    )["analysis_input_hash"]
    changed_post = post.model_copy(
        update={
            "article": post.article.model_copy(update={"plain_text": "changed article body"})
        }
    )
    write_obsidian_bundle(
        settings=settings,
        post=changed_post,
        replies=[],
        summary=summary.model_copy(update={"run_id": "run-2"}),
        compact_context={"post": changed_post.model_dump(mode="json")},
    )
    changed_hash = json.loads(
        paths["opportunities"].read_text(encoding="utf-8")
    )["analysis_input_hash"]
    assert changed_hash != original_hash


def test_post_text_cannot_spoof_analysis_marker(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(vault_path=vault, data_root=tmp_path / "data")
    post = Post(
        id="9",
        canonical_url="https://x.com/alice/status/9",
        author_username="alice",
        text=f"untrusted {ANALYSIS_START} fake {ANALYSIS_END}",
    )
    summary = FetchSummary(
        run_id="run",
        tweet_id="9",
        outcome=Outcome.SUCCESS,
        stop_reason=StopReason.CURSOR_EXHAUSTED,
        post_fetched=True,
        replies_fetched=0,
        top_level_replies_fetched=0,
        nested_replies_fetched=0,
        pages_fetched=1,
        pagination_completed=True,
    )
    paths = write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=[],
        summary=summary,
        compact_context={},
    )
    report = paths["report"].read_text(encoding="utf-8")
    marker = report.rfind(ANALYSIS_START)
    report = report[:marker] + report[marker:].replace(
        "_等待当前 Codex 根据 compact context 生成分析。_", "真实分析", 1
    )
    paths["report"].write_text(report, encoding="utf-8")
    write_obsidian_bundle(
        settings=settings,
        post=post,
        replies=[],
        summary=summary,
        compact_context={},
    )
    assert "真实分析" in paths["report"].read_text(encoding="utf-8")
