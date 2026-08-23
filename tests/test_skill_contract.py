from pathlib import Path

SKILLS_ROOT = Path(__file__).parents[1] / "skills"


def test_xbrief_uses_method_only_panel_and_fails_closed() -> None:
    xbrief = (SKILLS_ROOT / "xbrief" / "SKILL.md").read_text(encoding="utf-8")
    adapter = (
        SKILLS_ROOT / "xbrief" / "references" / "expert-panel.md"
    ).read_text(encoding="utf-8")

    assert "$nuwa-business-panel" in xbrief
    assert "$nuwa-business-panel" in adapter
    assert "Do not activate the upstream persona Skills directly" in xbrief
    assert "stop the analysis" in xbrief
    assert "Do not emit a full or partial expert-panel claim" in adapter

    for upstream in (
        "$feynman-perspective",
        "$paul-graham-perspective",
        "$munger-perspective",
    ):
        assert upstream not in xbrief
        assert upstream not in adapter


def test_nuwa_panel_keeps_persona_and_evidence_out_of_the_decision() -> None:
    panel = (SKILLS_ROOT / "nuwa-business-panel" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    sources = (
        SKILLS_ROOT / "nuwa-business-panel" / "references" / "sources.md"
    ).read_text(encoding="utf-8")

    assert "Never write as Feynman, Paul Graham, or Charlie Munger" in panel
    assert "Evidence records outrank every panel conclusion" in panel
    assert "generic question, feature request, or request for free advice is not E3" in panel
    assert "never use majority voting" in panel
    assert "Decision-conflict check" in panel
    assert "the single disputed assumption" in panel
    assert "not real-world decision accuracy" in panel
    assert "Audited commit" in sources
