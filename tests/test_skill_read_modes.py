"""Static contract regressions, not live agent/browser behavior tests."""

from pathlib import Path

ROOT = Path(__file__).parents[1] / "skills" / "xbrief"


def test_read_mode_cannot_implicitly_archive() -> None:
    skill = (ROOT / "SKILL.md").read_text()
    read = (ROOT / "references/read-only.md").read_text()
    assert "`READ`: default" in skill
    assert "`ARCHIVE`: only an explicit" in skill
    assert "抓取 alone does not authorize saving" in skill
    assert "Do not run doctor, prepare, configure" in read
    assert "Never use `xbrief prepare` as a read-only fetch" in skill
    assert "未归档" in read


def test_sparse_evidence_and_no_business_are_valid_outputs() -> None:
    read = (ROOT / "references/read-only.md").read_text()
    report = (ROOT / "references/report-format.md").read_text()
    skill = (ROOT / "SKILL.md").read_text()
    assert "评论未读取" in read
    assert "do not manufacture three comments" in read
    assert "`opportunities` empty and `recommended_execution` null" in report
    assert "未发现足够商业化证据" in skill
    assert "continue/adjust/stop" in skill


def test_interfaces_and_panel_support_read_only() -> None:
    for filename in ("interface.yaml", "openai.yaml"):
        text = (ROOT / "agents" / filename).read_text()
        assert "explicit" in text
    adapter = (ROOT / "references/expert-panel.md").read_text()
    assert "directly observed in-context evidence (READ)" in adapter
    assert "create nothing in READ" in adapter


def test_basic_summary_and_business_review_are_separate() -> None:
    read = (ROOT / "references/read-only.md").read_text()
    assert "Basic summaries and personal-use explanations" in read
    assert "explicit method-review requests require" in read
    assert "pause dependent conclusions" in read
    report = (ROOT / "references/report-format.md").read_text()
    assert "不适用（本次仅摘要）" in report
    assert "keep the requested full analysis incomplete" in report


def test_archive_preserves_capture_and_analysis_failure_boundaries() -> None:
    archive = (ROOT / "references/archive.md").read_text()
    assert "every capture check passes" in archive
    assert "Never bypass credential, backend or Vault failures" in archive
    assert "Saving alone does not require commercial analysis" in archive
    assert "preserve awaiting_analysis JSON/status" in archive
