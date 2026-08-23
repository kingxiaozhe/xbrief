from __future__ import annotations

import re
from pathlib import Path

_TOKEN_PATTERNS = (
    re.compile(r"(?i)(auth_token[\"'=:\s]+)[A-Za-z0-9%_-]{20,}"),
    re.compile(r"(?i)(ct0[\"'=:\s]+)[A-Fa-f0-9%_-]{20,}"),
)


def redact(text: str, cookie_path: Path | None = None) -> str:
    cleaned = text
    for pattern in _TOKEN_PATTERNS:
        cleaned = pattern.sub(r"\1[REDACTED]", cleaned)
    if cookie_path:
        cleaned = cleaned.replace(str(cookie_path), "[COOKIE_PATH]")
    return cleaned
