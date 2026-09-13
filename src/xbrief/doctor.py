from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from xbrief.adapters.twikit_cli import EXPECTED_TWIKIT_VERSION
from xbrief.config import Settings
from xbrief.security import cookie_file_safety


def run_doctor(settings: Settings) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    binary = shutil.which(settings.twikit_binary)
    checks.append(_check("twikit_binary", bool(binary), binary or "not found"))
    if binary:
        completed = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, check=False, timeout=10
        )
        version = (completed.stdout or completed.stderr).strip().splitlines()[-1:]
        version_text = version[0] if version else ""
        checks.append(
            _check(
                "twikit_version",
                completed.returncode == 0 and version_text.endswith(EXPECTED_TWIKIT_VERSION),
                f"{version_text} (expected {EXPECTED_TWIKIT_VERSION})",
            )
        )
        listed = subprocess.run(
            [binary, "list"], capture_output=True, text=True, check=False, timeout=10
        )
        tools = set(listed.stdout.splitlines())
        checks.append(
            _check(
                "readonly_tools",
                {
                    "get_tweet",
                    "get_tweet_replies",
                    "get_article_preview",
                    "get_article",
                }.issubset(tools),
                "get_tweet + get_tweet_replies + get_article_preview + get_article",
            )
        )

    checks.append(_cookie_check(settings.cookie_path))
    checks.append(_panel_skill_check())
    vault = settings.vault_path
    if vault is None:
        checks.append(
            _check(
                "obsidian_vault",
                False,
                "not configured; run xbrief configure --vault /absolute/path",
            )
        )
        checks.append(
            _check(
                "obsidian_writable",
                False,
                "not checked until an Obsidian Vault is configured",
            )
        )
        return {"ok": all(bool(item["ok"]) for item in checks), "checks": checks}

    checks.append(_check("obsidian_vault", vault.is_dir(), str(vault)))
    output_parent = vault / settings.vault_folder
    writable = os.access(vault, os.W_OK) if vault.exists() else False
    checks.append(_check("obsidian_writable", writable, str(output_parent)))
    return {"ok": all(bool(item["ok"]) for item in checks), "checks": checks}


def _cookie_check(path: Path) -> dict[str, object]:
    ok, detail = cookie_file_safety(path)
    return _check("cookie_file", ok, detail)


def _panel_skill_check() -> dict[str, object]:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    skill_file = codex_home / "skills" / "nuwa-business-panel" / "SKILL.md"
    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError:
        return _check("nuwa_business_panel", False, f"missing: {skill_file}")
    required = (
        "name: nuwa-business-panel",
        "Evidence records outrank every panel conclusion",
        "Never write as Feynman, Paul Graham, or Charlie Munger",
    )
    ok = content.startswith("---\n") and all(item in content for item in required)
    detail = str(skill_file) if ok else f"invalid contract: {skill_file}"
    return _check("nuwa_business_panel", ok, detail)


def _check(name: str, ok: bool, detail: str) -> dict[str, object]:
    return {"name": name, "ok": ok, "detail": detail}
