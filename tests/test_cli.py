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
