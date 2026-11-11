import hashlib
import hmac
import json

import pytest
from django.test import Client

from automations.models import Event
from integrations.models import Connection, InboundDelivery

pytestmark = pytest.mark.django_db

URL = "/hooks/github/"
SECRET = "whsec-test"


@pytest.fixture
def github_conn():
    return Connection.objects.create(provider="github", status="connected", credentials={"token": "t", "webhook_secret": SECRET})


def sign(body, secret=SECRET):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def post(client, event, payload, *, delivery="d-1", signature=None, raw=None):
    body = raw if raw is not None else json.dumps(payload).encode()
    return client.post(
        URL,
        data=body,
        content_type="application/json",
        HTTP_X_GITHUB_EVENT=event,
        HTTP_X_GITHUB_DELIVERY=delivery,
        HTTP_X_HUB_SIGNATURE_256=signature if signature is not None else sign(body),
    )


PUSH = {
    "ref": "refs/heads/main",
    "before": "aaa111",
    "after": "bbb222",
    "compare": "https://github.com/A1isherDev/atlas/compare/aaa111...bbb222",
    "commits": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
    "head_commit": {"id": "bbb222"},
    "repository": {"full_name": "A1isherDev/atlas", "name": "atlas", "private": False},
}

RELEASE = {
    "action": "published",
    "release": {"tag_name": "v2.0.0", "name": "Two", "html_url": "https://github.com/A1isherDev/atlas/releases/tag/v2.0.0"},
    "repository": {"full_name": "A1isherDev/atlas", "name": "atlas", "private": False},
}


def test_get_is_not_allowed(client):
    assert client.get(URL).status_code == 405


def test_csrf_is_not_required(github_conn):
    client = Client(enforce_csrf_checks=True)
    assert post(client, "ping", {"zen": "hi"}).status_code == 202


def test_bodies_over_one_megabyte_are_rejected(client, github_conn):
    body = b"{" + b" " * (1024 * 1024 + 1) + b"}"
    assert post(client, "push", None, raw=body).status_code == 413


def test_missing_secret_is_forbidden(client):
    Connection.objects.create(provider="github", status="connected", credentials={"token": "t"})
    assert post(client, "ping", {"zen": "hi"}).status_code == 403


def test_bad_signature_is_forbidden(client, github_conn):
    assert post(client, "push", PUSH, signature="sha256=" + "0" * 64).status_code == 403
    assert post(client, "push", PUSH, signature="").status_code == 403
    assert not Event.objects.exists()


def test_ping_is_accepted(client, github_conn):
    assert post(client, "ping", {"zen": "hi"}).status_code == 202
    assert not Event.objects.exists()


def test_push_is_stored_and_emitted(client, github_conn):
    assert post(client, "push", PUSH, delivery="d-push").status_code == 202
    delivery = InboundDelivery.objects.get(delivery_id="d-push")
    assert delivery.provider == "github"
    assert delivery.event == "push"
    assert delivery.status == InboundDelivery.Status.PROCESSED
    event = Event.objects.get(type="github.push")
    assert event.external_id == "ghd-d-push"
    assert event.source == "github"
    assert event.public is True
    assert event.payload == {
        "repo": "A1isherDev/atlas",
        "branch": "main",
        "commits": 3,
        "url": "https://github.com/A1isherDev/atlas/compare/aaa111...bbb222",
        "head": "bbb222",
    }


def test_duplicate_delivery_is_accepted_once(client, github_conn):
    post(client, "push", PUSH, delivery="d-dup")
    assert post(client, "push", PUSH, delivery="d-dup").status_code == 202
    assert Event.objects.count() == 1
    assert InboundDelivery.objects.count() == 1


def test_published_release_is_emitted(client, github_conn):
    assert post(client, "release", RELEASE, delivery="d-rel").status_code == 202
    event = Event.objects.get(type="github.release.published")
    assert event.external_id == "ghd-d-rel"
    assert event.payload == {"repo": "A1isherDev/atlas", "tag": "v2.0.0", "name": "Two", "url": "https://github.com/A1isherDev/atlas/releases/tag/v2.0.0"}


def test_other_release_actions_are_ignored(client, github_conn):
    assert post(client, "release", {**RELEASE, "action": "edited"}).status_code == 202
    assert not Event.objects.exists()
    assert InboundDelivery.objects.get().status == InboundDelivery.Status.IGNORED


def test_private_repo_pushes_stay_out_of_the_public_feed(client, github_conn):
    post(client, "push", {**PUSH, "repository": {**PUSH["repository"], "private": True}})
    assert Event.objects.get().public is False


def test_unknown_events_are_ignored(client, github_conn):
    assert post(client, "issues", {"action": "opened"}).status_code == 202
    assert not Event.objects.exists()


def test_invalid_json_is_a_bad_request(client, github_conn):
    assert post(client, "push", None, raw=b"not json").status_code == 400


def test_missing_delivery_id_is_a_bad_request(client, github_conn):
    assert post(client, "push", PUSH, delivery="").status_code == 400
