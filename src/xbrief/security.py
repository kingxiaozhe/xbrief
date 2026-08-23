from __future__ import annotations

import stat
from pathlib import Path


def cookie_file_safety(path: Path) -> tuple[bool, str]:
    if not path.exists() and not path.is_symlink():
        return False, "not configured"
    try:
        file_stat = path.lstat()
        parent_stat = path.parent.lstat()
    except OSError:
        return False, "cannot inspect cookie metadata"
    if stat.S_ISLNK(file_stat.st_mode) or stat.S_ISLNK(parent_stat.st_mode):
        return False, "symbolic links are not allowed"
    if not stat.S_ISREG(file_stat.st_mode):
        return False, "cookie path is not a regular file"
    if not stat.S_ISDIR(parent_stat.st_mode):
        return False, "cookie parent is not a directory"
    file_mode = stat.S_IMODE(file_stat.st_mode)
    parent_mode = stat.S_IMODE(parent_stat.st_mode)
    ok = file_mode == 0o600 and parent_mode == 0o700
    return ok, f"file={oct(file_mode)} directory={oct(parent_mode)}"
