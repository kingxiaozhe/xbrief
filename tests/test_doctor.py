from pathlib import Path

from xbrief.config import Settings
from xbrief.doctor import _panel_skill_check, run_doctor


def test_panel_skill_check_uses_codex_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    missing = _panel_skill_check()
    assert missing == {
        "name": "nuwa_business_panel",
        "ok": False,
        "detail": f"missing: {tmp_path / 'skills' / 'nuwa-business-panel' / 'SKILL.md'}",
    }

    skill_file = tmp_path / "skills" / "nuwa-business-panel" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("---\nname: nuwa-business-panel\n---\n", encoding="utf-8")
    invalid = _panel_skill_check()
    assert invalid["ok"] is False
    assert str(invalid["detail"]).startswith("invalid contract:")

    source = (
        Path(__file__).parents[1] / "skills" / "nuwa-business-panel" / "SKILL.md"
    )
    skill_file.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    installed = _panel_skill_check()
    assert installed["ok"] is True


def test_doctor_reports_missing_vault_without_local_default(monkeypatch) -> None:
    monkeypatch.delenv("XBRIEF_VAULT", raising=False)
    settings = Settings()
    assert settings.vault_path is None

    result = run_doctor(settings)
    checks = {item["name"]: item for item in result["checks"]}
    assert checks["obsidian_vault"] == {
        "name": "obsidian_vault",
        "ok": False,
        "detail": "not configured; run xbrief configure --vault /absolute/path",
    }
