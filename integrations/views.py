"""Inbound webhooks from services."""
import hashlib
import hmac
import json

from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from automations.events import emit

from .models import Connection, InboundDelivery
from .providers.github import already_recorded, push_payload, release_payload

MAX_BODY_BYTES = 1024 * 1024


def _too_large():
    return HttpResponse("Payload too large.", status=413)


def _accepted(note="Accepted."):
    return HttpResponse(note, status=202)


def _signature_ok(secret, body, header):
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


@csrf_exempt
@require_POST
def github_webhook(request):
    try:
        declared = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        declared = 0
    if declared > MAX_BODY_BYTES:
        return _too_large()
    body = request.body
    if len(body) > MAX_BODY_BYTES:
        return _too_large()

    connection = Connection.objects.filter(provider="github").first()
    secret = (connection.credentials.get("webhook_secret") if connection else "") or ""
    if not _signature_ok(secret, body, request.headers.get("X-Hub-Signature-256", "")):
        return HttpResponseForbidden("Signature missing or invalid.")

    event_name = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    if not delivery_id:
        return HttpResponseBadRequest("Missing X-GitHub-Delivery.")
    if event_name == "ping":
        return _accepted("pong")
    try:
        payload = json.loads(body)
    except ValueError:
        return HttpResponseBadRequest("Body is not JSON.")
    if not isinstance(payload, dict):
        return HttpResponseBadRequest("Body is not a JSON object.")

    try:
        with transaction.atomic():
            delivery = InboundDelivery.objects.create(provider="github", delivery_id=delivery_id[:120], event=event_name[:60], payload=payload)
    except IntegrityError:
        return _accepted("Already received.")

    status = _handle(event_name, delivery_id, payload)
    InboundDelivery.objects.filter(pk=delivery.pk).update(status=status, processed_at=timezone.now())
    return _accepted()


def _handle(event_name, delivery_id, payload):
    repository = payload.get("repository") or {}
    repo = repository.get("full_name", "")
    if event_name == "push" and not payload.get("deleted"):
        commits = payload.get("commits")
        data = push_payload(
            repo, payload.get("ref"), payload.get("after"), payload.get("before"),
            len(commits) if isinstance(commits, list) else None, payload.get("compare"),
        )
        type = "github.push"
    elif event_name == "release" and payload.get("action") == "published":
        data, type = release_payload(repo, payload.get("release") or {}), "github.release.published"
    else:
        return InboundDelivery.Status.IGNORED
    if data is None or already_recorded(type, data):
        return InboundDelivery.Status.IGNORED
    emit(type, data, source="github", external_id=f"ghd-{delivery_id}", public=not repository.get("private", False))
    return InboundDelivery.Status.PROCESSED
