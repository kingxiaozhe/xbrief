from __future__ import annotations


class XBriefError(RuntimeError):
    """A structured, safe-to-display xbrief failure."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


EXIT_CODES = {
    "invalid_url": 2,
    "config_error": 2,
    "auth_failed": 3,
    "not_found": 4,
    "restricted": 4,
    "backend_error": 5,
    "storage_error": 6,
}


def exit_code_for(error: XBriefError) -> int:
    return EXIT_CODES.get(error.code, 5)
