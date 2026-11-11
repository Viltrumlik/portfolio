import hashlib
import hmac
import json

import httpx
import pytest

from automations.models import Event
from integrations.errors import Permanent, Transient
from integrations.models import OutboundHook
from integrations.providers import webhook

pytestmark = pytest.mark.django_db

URL = "https://n8n.example.com/webhook/atlas"
PINNED = "https://93.184.216.34/webhook/atlas"  # requests go to the validated address, not the name


@pytest.fixture
def hook():
    return OutboundHook.objects.create(name="n8n", url=URL, secret={"secret": "s3cret"}, events=["contact.submitted"])


@pytest.fixture
def event():
    return Event.objects.create(type="contact.submitted", payload={"name": "Ann", "message": "Hi"})


def test_deliver_posts_signed_json(api, resolve_to, hook, event):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=200, json={})

    webhook.deliver(hook, event)

    request = api.requests[0]
    body = json.loads(request.content)
    assert body == {"id": event.pk, "type": "contact.submitted", "occurred_at": event.occurred_at.isoformat(), "data": {"name": "Ann", "message": "Hi"}}
    assert request.headers["X-Atlas-Event"] == "contact.submitted"
    assert request.headers["X-Atlas-Delivery"]
    expected = "sha256=" + hmac.new(b"s3cret", request.content, hashlib.sha256).hexdigest()
    assert request.headers["X-Atlas-Signature"] == expected
    assert request.headers["Content-Type"] == "application/json"
    hook.refresh_from_db()
    assert hook.last_status_code == 200
    assert hook.last_delivery_at is not None


def test_delivery_id_is_stable_across_retries(api, resolve_to, hook, event):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=200, json={})
    webhook.deliver(hook, event)
    webhook.deliver(hook, event)
    assert api.requests[0].headers["X-Atlas-Delivery"] == api.requests[1].headers["X-Atlas-Delivery"]


@pytest.mark.parametrize("status", [500, 503, 429])
def test_server_errors_and_429_are_transient(api, resolve_to, hook, event, status):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=status, json={})
    with pytest.raises(Transient):
        webhook.deliver(hook, event)
    hook.refresh_from_db()
    assert hook.last_status_code == status


@pytest.mark.parametrize("status", [400, 404, 410])
def test_other_client_errors_are_permanent(api, resolve_to, hook, event, status):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=status, json={})
    with pytest.raises(Permanent, match=str(status)):
        webhook.deliver(hook, event)


def test_redirects_are_not_followed(api, resolve_to, hook, event):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=302, headers={"Location": "http://169.254.169.254/"})
    with pytest.raises(Permanent, match="redirect"):
        webhook.deliver(hook, event)
    assert len(api.requests) == 1


def test_timeouts_are_transient(api, resolve_to, hook, event):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, httpx.ReadTimeout("slow"))
    with pytest.raises(Transient):
        webhook.deliver(hook, event)


def test_private_targets_are_refused_before_any_request(api, resolve_to, hook, event):
    resolve_to("10.0.0.7")
    with pytest.raises(Permanent):
        webhook.deliver(hook, event)
    assert api.requests == []


def test_hook_without_a_secret_is_permanent(api, resolve_to, event):
    resolve_to("93.184.216.34")
    hook = OutboundHook.objects.create(name="bare", url=URL, secret={}, events=[])
    with pytest.raises(Permanent, match="secret"):
        webhook.deliver(hook, event)


def test_send_ping_posts_a_signed_ping(api, resolve_to, hook):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=204)
    assert webhook.send_ping(hook) == 204
    request = api.requests[0]
    assert request.headers["X-Atlas-Event"] == "ping"
    assert json.loads(request.content)["type"] == "ping"
    expected = "sha256=" + hmac.new(b"s3cret", request.content, hashlib.sha256).hexdigest()
    assert request.headers["X-Atlas-Signature"] == expected


# --- DNS pinning: the request goes to the address that was validated ---------------------


@pytest.fixture
def dns_answers(monkeypatch):
    """Answer successive lookups from a list (a rebinding attacker's DNS); record each lookup."""
    from integrations import netguard

    def install(*answers):
        queue, lookups = list(answers), []

        def fake(host, port, *args, **kwargs):
            lookups.append(host)
            address = queue.pop(0) if len(queue) > 1 else queue[0]
            return [(2, 1, 6, "", (address, port))]

        monkeypatch.setattr(netguard, "_getaddrinfo", fake)
        return lookups

    return install


def test_request_goes_to_the_validated_ip_even_if_dns_changes(api, dns_answers, hook, event):
    lookups = dns_answers("93.184.216.34", "127.0.0.1")  # a second lookup would say loopback
    api.add("POST", PINNED, status=200, json={})
    webhook.deliver(hook, event)
    assert str(api.requests[0].url) == PINNED
    assert lookups == ["n8n.example.com"]  # resolved once, never again


def test_host_header_and_sni_carry_the_original_hostname(api, resolve_to, hook, event):
    resolve_to("93.184.216.34")
    api.add("POST", PINNED, status=200, json={})
    webhook.deliver(hook, event)
    request = api.requests[0]
    assert request.headers["Host"] == "n8n.example.com"
    assert request.extensions["sni_hostname"] == "n8n.example.com"


def test_non_default_ports_are_kept(api, resolve_to, event):
    resolve_to("93.184.216.34")
    hook = OutboundHook.objects.create(name="p", url="https://n8n.example.com:8443/h", secret={"secret": "s"})
    api.add("POST", "https://93.184.216.34:8443/h", status=200, json={})
    webhook.deliver(hook, event)
    assert api.requests[0].headers["Host"] == "n8n.example.com:8443"


def test_ipv6_answers_are_pinned_too(api, resolve_to, hook, event):
    resolve_to("2606:2800:220:1:248:1893:25c8:1946")
    api.add("POST", "https://[2606:2800:220:1:248:1893:25c8:1946]/webhook/atlas", status=200, json={})
    webhook.deliver(hook, event)
    assert api.requests[0].headers["Host"] == "n8n.example.com"


@pytest.mark.parametrize("address", ["127.0.0.1", "10.1.2.3", "169.254.169.254", "::1", "::ffff:127.0.0.1"])
def test_private_and_loopback_answers_are_still_rejected(api, resolve_to, hook, event, address):
    resolve_to(address)
    with pytest.raises(Permanent):
        webhook.deliver(hook, event)
    assert api.requests == []


def test_real_httpx_transport_connects_to_the_pinned_ip_and_sends_sni(resolve_to, hook, event):
    """Through real httpx + httpcore (only the socket layer is faked): TCP to the IP, TLS SNI = hostname."""
    import httpcore

    from integrations import http

    seen = {}

    class Stream(httpcore.MockStream):
        def write(self, buffer, timeout=None):
            seen.setdefault("sent", b"")
            seen["sent"] += buffer

        def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            seen["sni"] = server_hostname
            seen["check_hostname"] = ssl_context.check_hostname
            return self

    class Backend(httpcore.MockBackend):
        def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
            seen["connect"] = (host, port)
            return Stream(list(self._buffer))

    resolve_to("93.184.216.34")
    transport = httpx.HTTPTransport()
    transport._pool._network_backend = Backend([b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"])
    with http.use_transport(transport):
        assert webhook.deliver(hook, event) == 200
    assert seen["connect"] == ("93.184.216.34", 443)
    assert seen["sni"] == "n8n.example.com"
    assert seen["check_hostname"] is True
    assert b"\r\nHost: n8n.example.com\r\n" in seen["sent"]
