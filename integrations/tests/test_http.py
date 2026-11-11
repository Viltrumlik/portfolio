import httpx
import pytest
from django.test import override_settings

from integrations import http
from integrations.errors import AuthError, Permanent, RateLimited, Transient


def test_rate_limited_carries_retry_after():
    exc = RateLimited(42, "slow down")
    assert exc.retry_after_seconds == 42
    assert str(exc) == "slow down"


def test_errors_carry_an_optional_code():
    assert AuthError("GitHub rejected the token.", code="401").code == "401"
    assert Permanent("nope").code == ""
    assert issubclass(Transient, Exception)


@override_settings(ATLAS_HTTP_TIMEOUT=7)
def test_client_uses_timeout_user_agent_and_no_redirects():
    with http.client() as c:
        assert c.timeout.read == 7
        assert c.headers["User-Agent"] == "atlas-portfolio"
        assert c.follow_redirects is False


def test_use_transport_routes_requests_through_the_mock():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with http.use_transport(httpx.MockTransport(handler)):
        with http.client() as c:
            assert c.get("https://example.com/x").json() == {"ok": True}
    assert seen[0].headers["User-Agent"] == "atlas-portfolio"


def test_request_turns_timeouts_into_transient(api):
    api.add("GET", "https://example.com/", httpx.ReadTimeout("slow"))
    with pytest.raises(Transient) as info:
        http.request("GET", "https://example.com/", service="Example")
    assert "Example" in str(info.value)


def test_unmocked_requests_never_reach_the_network():
    with pytest.raises(AssertionError):
        http.request("GET", "https://example.com/", service="Example")
