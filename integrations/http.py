"""Outgoing HTTP to providers. Every call goes through `client()` so tests can swap the transport."""
from contextlib import contextmanager

import httpx
from django.conf import settings

from .errors import Transient

USER_AGENT = "atlas-portfolio"

_transport = None  # test seam: an httpx.MockTransport installed by use_transport()


def client(**kwargs):
    """An httpx.Client with the site's timeout, User-Agent and no redirect following."""
    headers = {"User-Agent": USER_AGENT, **kwargs.pop("headers", {})}
    return httpx.Client(
        timeout=settings.ATLAS_HTTP_TIMEOUT,
        headers=headers,
        follow_redirects=False,
        transport=_transport,
        **kwargs,
    )


@contextmanager
def use_transport(transport):
    """Route every client() through `transport` (e.g. httpx.MockTransport) inside the block."""
    global _transport
    previous, _transport = _transport, transport
    try:
        yield transport
    finally:
        _transport = previous


def request(method, url, *, service, **kwargs):
    """Send one request. Network failures become Transient with a message that never includes the URL."""
    try:
        with client() as c:
            return c.request(method, url, **kwargs)
    except httpx.TimeoutException as exc:
        raise Transient(f"{service} did not answer in time. It will retry.", code="timeout") from exc
    except httpx.TransportError as exc:
        raise Transient(f"{service} could not be reached. It will retry.", code="network") from exc
