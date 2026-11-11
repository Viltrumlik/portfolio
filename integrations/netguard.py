"""SSRF guard for owner-supplied URLs (outgoing webhooks).

`pin(url)` resolves the host once, rejects anything but public addresses, and returns a URL that
points at the validated IP. The caller sends the original name in the Host header and as the TLS
SNI (`extensions={"sni_hostname": ...}`), so the certificate is still checked against the real
hostname while no second DNS lookup can redirect the connection (DNS rebinding). The HTTP client
never follows redirects, so a public endpoint cannot bounce a delivery to an internal one either.
"""
import ipaddress
import re
import socket
from dataclasses import dataclass

import httpx

from .errors import Permanent

_getaddrinfo = socket.getaddrinfo  # test seam
_HOSTNAME = re.compile(r"^(?=.{1,253}$)([a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?)(\.[a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?)*\.?$")


@dataclass(frozen=True)
class PinnedTarget:
    url: str  # the original URL with its host replaced by `address`
    address: str  # the validated IP the request must connect to
    host_header: str  # original host[:port] for the Host header
    sni_hostname: str | None  # original hostname for TLS SNI / certificate checks (None for IP literals)


def _is_public(address):
    ip = ipaddress.ip_address(address.split("%", 1)[0])
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
        or not ip.is_global
    )


def _is_ip_literal(host):
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def pin(url):
    """Validate `url` and pin it to one public address. Raises Permanent otherwise."""
    try:
        parsed = httpx.URL(url or "")
    except (httpx.InvalidURL, TypeError) as exc:
        raise Permanent("The webhook URL is not valid.", code="url") from exc
    if parsed.scheme != "https":
        raise Permanent("Webhook URLs must use https.", code="url")
    host = parsed.raw_host.decode("ascii").lower()  # IDNA-encoded, lowercase
    if not host:
        raise Permanent("The webhook URL has no host.", code="url")
    if not (_HOSTNAME.match(host) or _is_ip_literal(host)) or not 0 < (parsed.port or 443) < 65536:
        raise Permanent("The webhook URL is not valid.", code="url")
    if parsed.userinfo:
        raise Permanent("Put webhook credentials in the signing secret, not in the URL.", code="url")
    try:
        infos = _getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError) as exc:
        raise Permanent(f"Could not resolve {host}. Check the webhook URL.", code="dns") from exc
    addresses = [info[4][0] for info in infos]
    if not addresses:
        raise Permanent(f"Could not resolve {host}. Check the webhook URL.", code="dns")
    for address in addresses:
        if not _is_public(address):
            raise Permanent(f"{host} points to a private or reserved address; webhooks must be public.", code="ssrf")
    address = addresses[0].split("%", 1)[0]
    return PinnedTarget(
        url=str(parsed.copy_with(host=address)),
        address=address,
        host_header=parsed.netloc.decode("ascii").lower(),
        sni_hostname=None if _is_ip_literal(host) else host,
    )


def check_url(url):
    """Raise Permanent unless `url` is https and its host resolves only to public addresses."""
    return pin(url)
