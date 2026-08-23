from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from xbrief.errors import XBriefError


def _config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def _data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def _vault_from_env() -> Path | None:
    value = os.environ.get("XBRIEF_VAULT")
    return Path(value).expanduser() if value else None


class Settings(BaseModel):
    vault_path: Path | None = Field(default_factory=_vault_from_env)
    vault_folder: str = "XBrief"
    data_root: Path = Field(default_factory=lambda: _data_home() / "xbrief")
    cookie_path: Path = Field(
        default_factory=lambda: _config_home() / "twitter-mcp" / "cookies.json"
    )
    account_alias: str = "dedicated-1"
    twikit_binary: str = "twikit-mcp"
    include_nested: bool = True
    max_depth: int = 3
    max_pages: int = 250
    max_replies: int = 1000
    max_comments_for_model: int = 24
    max_model_input_chars: int = 16000
    comments_per_note: int = 200
    subprocess_timeout_seconds: int = 45

    @property
    def database_path(self) -> Path:
        return self.data_root / "xbrief.sqlite3"

    @property
    def config_path(self) -> Path:
        return _config_home() / "xbrief" / "config.json"

    def require_vault(self) -> Path:
        if self.vault_path is None:
            raise XBriefError(
                "config_error",
                "未配置 Obsidian Vault。请先运行：xbrief configure --vault /你的/Vault/路径",
            )
        return self.vault_path


def load_settings() -> Settings:
    path = _config_home() / "xbrief" / "config.json"
    if not path.exists():
        return Settings()
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return Settings.model_validate(payload)
    except (OSError, ValueError) as exc:
        raise XBriefError("config_error", f"无法读取配置：{path}") from exc


def save_settings(settings: Settings) -> Path:
    path = settings.config_path
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(settings.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path
