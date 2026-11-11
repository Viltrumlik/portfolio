"""Typed failures from connected services. The job runner decides retries from the type.

Messages are human sentences that are safe to show the owner (never include a secret).
`code` is the service's own error code ("401", "lastfm-10") for `Connection.error_code`.
"""


class IntegrationError(Exception):
    def __init__(self, message="", *, code=""):
        super().__init__(message)
        self.code = str(code or "")


class AuthError(IntegrationError):
    """The credentials were rejected. Fail now; the owner must reconnect."""


class Permanent(IntegrationError):
    """Retrying will not help (bad request, missing permission, misconfiguration)."""


class Transient(IntegrationError):
    """A temporary failure (timeout, 5xx). Retry with backoff."""


class RateLimited(IntegrationError):
    """The service asked us to slow down. Retry after `retry_after_seconds`."""

    def __init__(self, retry_after_seconds, message="", *, code="429"):
        super().__init__(message or f"Rate limited; retry in {retry_after_seconds}s.", code=code)
        self.retry_after_seconds = max(1, int(retry_after_seconds or 1))
