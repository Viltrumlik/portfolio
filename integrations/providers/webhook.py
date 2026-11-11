"""Outgoing webhooks (n8n, Make, Zapier): signed JSON POSTs to owner-supplied https URLs."""
import hashlib
import hmac
import json
import uuid

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from .. import http, netguard
from ..errors import Permanent, Transient
from ..models import OutboundHook


def sign(secret, body):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _post(hook, event_type, delivery_id, document):
    secret = (hook.secret or {}).get("secret")
    if not secret:
        raise Permanent(f"Webhook “{hook.name}” has no signing secret. Add one and try again.", code="no_secret")
    # Resolve once and connect to that exact address: a second DNS answer can't redirect us inward.
    target = netguard.pin(hook.url)
    body = json.dumps(document, cls=DjangoJSONEncoder, separators=(",", ":")).encode()
    headers = {
        "Host": target.host_header,
        "Content-Type": "application/json",
        "X-Atlas-Event": event_type,
        "X-Atlas-Delivery": delivery_id,
        "X-Atlas-Signature": sign(secret, body),
    }
    extensions = {"sni_hostname": target.sni_hostname} if target.sni_hostname else {}
    try:
        response = http.request(
            "POST", target.url, service=f"Webhook “{hook.name}”", content=body, headers=headers, extensions=extensions
        )
    except Transient:
        OutboundHook.objects.filter(pk=hook.pk).update(last_status_code=None, last_delivery_at=timezone.now())
        raise
    status = response.status_code
    OutboundHook.objects.filter(pk=hook.pk).update(last_status_code=status, last_delivery_at=timezone.now())
    hook.last_status_code = status
    if 200 <= status < 300:
        return status
    if 300 <= status < 400:
        raise Permanent(f"Webhook “{hook.name}” answered with a redirect ({status}). Use the final URL.", code=str(status))
    if status == 429 or status >= 500:
        raise Transient(f"Webhook “{hook.name}” answered {status}. It will retry.", code=str(status))
    raise Permanent(f"Webhook “{hook.name}” answered {status}. Check the URL and the receiving workflow.", code=str(status))


def deliver(hook, event):
    """POST {id, type, occurred_at, data} for `event`. Same X-Atlas-Delivery on every retry."""
    document = {"id": event.pk, "type": event.type, "occurred_at": event.occurred_at.isoformat(), "data": event.payload}
    return _post(hook, event.type, f"evt-{event.pk}-hook-{hook.pk}", document)


def send_ping(hook):
    """POST a signed ping. Returns the status code."""
    document = {"id": None, "type": "ping", "occurred_at": timezone.now().isoformat(), "data": {"hook": hook.name}}
    return _post(hook, "ping", f"ping-{uuid.uuid4().hex}", document)
