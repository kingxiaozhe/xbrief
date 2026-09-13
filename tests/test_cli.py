import json

import pytest
from typer.testing import CliRunner

from xbrief.cli import app

runner = CliRunner()


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "xbrief 0.1.0"


def test_prepare_rejects_invalid_url_as_json() -> None:
    result = runner.invoke(app, ["prepare", "--json", "https://example.com/nope"])
    assert result.exit_code == 2
    assert '"error_code": "invalid_url"' in result.stdout


def test_prepare_hides_unexpected_internal_error(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise OSError("private local path")

    monkeypatch.setattr("xbrief.cli.prepare_service", fail)
    result = runner.invoke(app, ["prepare", "--json", "https://x.com/alice/status/1"])
    assert result.exit_code == 6
    assert "private local path" not in result.stdout
    assert '"error_code": "storage_error"' in result.stdout


def test_prepare_requires_a_configured_vault(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("XBRIEF_VAULT", raising=False)

    result = runner.invoke(app, ["prepare", "--json", "https://x.com/alice/status/1"])

    assert result.exit_code == 2
    assert '"error_code": "config_error"' in result.stdout
    assert "未配置 Obsidian Vault" in result.stdout


@pytest.mark.parametrize("config_text", ["{broken", '{"max_pages": "invalid"}'])
@pytest.mark.parametrize("json_output", [True, False])
def test_doctor_config_error(monkeypatch, tmp_path, config_text, json_output) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("XBRIEF_VAULT", raising=False)
    config_path = tmp_path / "xbrief" / "config.json"
    config_path.parent.mkdir()
    config_path.write_text(config_text, encoding="utf-8")

    def unexpected_doctor(_settings):
        pytest.fail("Invalid configuration must stop before doctor checks")

    monkeypatch.setattr("xbrief.cli.run_doctor", unexpected_doctor)
    result = runner.invoke(app, ["doctor", "--json"] if json_output else ["doctor"])

    assert result.exit_code == 2
    message = f"无法读取配置：{config_path}"
    if json_output:
        assert json.loads(result.stdout) == {
            "ok": False, "error_code": "config_error", "message": message
        }
    else:
        assert result.stdout.strip() == message


@pytest.mark.parametrize("ok", [True, False])
@pytest.mark.parametrize("json_output", [True, False])
def test_doctor_preserves_check_output(monkeypatch, tmp_path, ok, json_output) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("XBRIEF_VAULT", raising=False)
    payload = {"ok": ok, "checks": [{"name": "offline", "ok": ok, "detail": "isolated"}]}
    monkeypatch.setattr("xbrief.cli.run_doctor", lambda _settings: payload)

    result = runner.invoke(app, ["doctor", "--json"] if json_output else ["doctor"])

    assert result.exit_code == (0 if ok else 2)
    if json_output:
        assert json.loads(result.stdout) == payload
    else:
        assert result.stdout.strip() == f"{'✓' if ok else '✗'} offline: isolated"
