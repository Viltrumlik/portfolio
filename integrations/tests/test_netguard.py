import pytest

from integrations import netguard
from integrations.errors import Permanent


def test_public_https_url_is_allowed(resolve_to):
    resolve_to("93.184.216.34")
    netguard.check_url("https://hooks.example.com/webhook/abc")


def test_plain_http_is_rejected(resolve_to):
    resolve_to("93.184.216.34")
    with pytest.raises(Permanent, match="https"):
        netguard.check_url("http://hooks.example.com/webhook")


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.0.0.5", "192.168.1.2", "172.16.0.1", "169.254.169.254", "0.0.0.0", "224.0.0.1", "::1", "fe80::1", "fc00::1", "240.0.0.1"],
)
def test_internal_addresses_are_rejected(resolve_to, address):
    resolve_to(address)
    with pytest.raises(Permanent):
        netguard.check_url("https://hooks.example.com/x")


def test_any_bad_address_among_several_is_rejected(resolve_to):
    resolve_to("93.184.216.34", "10.0.0.1")
    with pytest.raises(Permanent):
        netguard.check_url("https://hooks.example.com/x")


def test_ip_literal_hosts_are_checked_too(resolve_to):
    resolve_to("127.0.0.1")
    with pytest.raises(Permanent):
        netguard.check_url("https://127.0.0.1/x")


def test_unresolvable_host_is_rejected(monkeypatch):
    import socket

    def fail(*a, **k):
        raise socket.gaierror("nope")

    monkeypatch.setattr(netguard, "_getaddrinfo", fail)
    with pytest.raises(Permanent, match="resolve"):
        netguard.check_url("https://nowhere.invalid/x")


def test_url_without_host_or_with_credentials_is_rejected(resolve_to):
    resolve_to("93.184.216.34")
    with pytest.raises(Permanent):
        netguard.check_url("https:///path")
    with pytest.raises(Permanent):
        netguard.check_url("https://user:pass@hooks.example.com/x")


def test_pin_returns_the_validated_address_with_the_original_host(resolve_to):
    resolve_to("93.184.216.34")
    target = netguard.pin("https://Hooks.Example.com/path?q=1")
    assert target.url == "https://93.184.216.34/path?q=1"
    assert target.address == "93.184.216.34"
    assert target.host_header == "hooks.example.com"
    assert target.sni_hostname == "hooks.example.com"


def test_pin_keeps_ip_literal_hosts_without_sni(resolve_to):
    resolve_to("93.184.216.34")
    target = netguard.pin("https://93.184.216.34/x")
    assert target.url == "https://93.184.216.34/x"
    assert target.sni_hostname is None


def test_pin_rejects_bad_urls(resolve_to):
    resolve_to("93.184.216.34")
    with pytest.raises(Permanent):
        netguard.pin("https://exa mple.com:99999/")
