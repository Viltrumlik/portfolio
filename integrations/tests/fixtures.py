"""Shared test fixtures: no real network, and a small fake API router for httpx."""
import json as jsonlib
import re

import httpx
import pytest

from integrations import http, netguard


class FakeAPI:
    """Route httpx requests to canned responses. Unmatched requests fail the test."""

    def __init__(self):
        self.routes = []
        self.requests = []

    def add(self, method, url, response=None, *, json=None, status=200, headers=None, match=None, times=None):
        """Register a route. `url` is a prefix (or a compiled regex); `response` may be a callable(request)."""
        self.routes.append(
            {
                "method": method.upper(),
                "url": url,
                "response": response,
                "json": json,
                "status": status,
                "headers": headers or {},
                "match": match,
                "times": times,
            }
        )
        return self

    def _matches(self, route, request):
        if route["method"] != request.method:
            return False
        target = str(request.url)
        if isinstance(route["url"], re.Pattern):
            if not route["url"].search(target):
                return False
        elif not target.startswith(route["url"]):
            return False
        if route["times"] == 0:
            return False
        return route["match"] is None or route["match"](request)

    def __call__(self, request):
        self.requests.append(request)
        for route in self.routes:
            if self._matches(route, request):
                if route["times"] is not None:
                    route["times"] -= 1
                if callable(route["response"]):
                    return route["response"](request)
                if isinstance(route["response"], Exception):
                    raise route["response"]
                return httpx.Response(route["status"], json=route["json"], headers=route["headers"])
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    def calls(self, method=None, contains=""):
        return [r for r in self.requests if (method is None or r.method == method) and contains in str(r.url)]


def body_json(request):
    return jsonlib.loads(request.content.decode() or "{}")


def _refuse(request):
    raise AssertionError(f"Tests must not hit the network: {request.method} {request.url}")


def _refuse_dns(host, port, *args, **kwargs):
    raise AssertionError(f"Tests must not resolve hosts: {host}")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(netguard, "_getaddrinfo", _refuse_dns)
    with http.use_transport(httpx.MockTransport(_refuse)):
        yield


@pytest.fixture
def api():
    fake = FakeAPI()
    with http.use_transport(httpx.MockTransport(fake)):
        yield fake


@pytest.fixture
def resolve_to(monkeypatch):
    """resolve_to("93.184.216.34") makes every DNS lookup return that address."""

    def install(*addresses):
        def fake(host, port, *args, **kwargs):
            return [(2, 1, 6, "", (addr, port or 443)) for addr in addresses]

        monkeypatch.setattr(netguard, "_getaddrinfo", fake)

    return install
