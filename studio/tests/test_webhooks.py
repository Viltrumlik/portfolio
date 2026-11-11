"""Outgoing webhooks: list, create, edit (secret is write-only), send a test, delete."""
import pytest

from integrations.models import OutboundHook

pytestmark = pytest.mark.django_db

PINNED = "https://93.184.216.34/hook"  # deliveries go to the validated address, not the name
NEW = {"name": "n8n", "url": "https://n8n.example.com/hook", "secret": "s3cret-abcd", "events": ["contact.submitted", "post.published"], "is_active": "on"}


def html(response, status=200):
    assert response.status_code == status, response.status_code
    return response.content.decode()


def test_list_shows_hooks_with_a_masked_secret(staff):
    OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/hook", secret={"secret": "s3cret-abcd"}, events=["post.published"])
    page = html(staff.get("/studio/webhooks/"))
    assert "n8n" in page and "https://n8n.example.com/hook" in page and "post.published" in page
    assert "s3cret-abcd" not in page and "•••• abcd" in page
    assert "Send test" in page
    for event in ("github.push", "github.release.published", "contact.submitted", "post.published", "sync.failed"):
        assert f'value="{event}"' in page  # the create form's event checkboxes


def test_create_a_hook(staff):
    r = staff.post("/studio/webhooks/", NEW)
    assert r.status_code == 302 and r["Location"] == "/studio/webhooks/"
    hook = OutboundHook.objects.get()
    assert (hook.name, hook.url, hook.secret, hook.events, hook.is_active) == (
        "n8n", "https://n8n.example.com/hook", {"secret": "s3cret-abcd"}, ["contact.submitted", "post.published"], True)


def test_create_requires_https_and_a_secret(staff):
    page = html(staff.post("/studio/webhooks/", {**NEW, "url": "http://n8n.example.com/hook", "secret": ""}))
    assert "Use an https:// URL." in page
    assert "Add a signing secret" in page
    assert not OutboundHook.objects.exists()


def test_unknown_events_are_rejected(staff):
    page = html(staff.post("/studio/webhooks/", {**NEW, "events": ["user.deleted"]}))
    assert "Select a valid choice" in page
    assert not OutboundHook.objects.exists()


def test_edit_keeps_the_secret_when_left_empty(staff):
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/hook", secret={"secret": "keep-me1"}, events=["post.published"])
    page = html(staff.get(f"/studio/webhooks/{hook.pk}/"))
    assert "keep-me1" not in page and "•••• -me1" in page
    r = staff.post(f"/studio/webhooks/{hook.pk}/", {"name": "Make", "url": "https://hook.make.com/x", "secret": "", "events": ["github.push"]})
    assert r.status_code == 302
    hook.refresh_from_db()
    assert (hook.name, hook.url, hook.secret, hook.events, hook.is_active) == ("Make", "https://hook.make.com/x", {"secret": "keep-me1"}, ["github.push"], False)


def test_edit_replaces_the_secret(staff):
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/hook", secret={"secret": "old"})
    staff.post(f"/studio/webhooks/{hook.pk}/", {**NEW, "secret": "new-secret"})
    hook.refresh_from_db()
    assert hook.secret == {"secret": "new-secret"}


def test_send_test_shows_the_status_code(staff, api, resolve_to):
    resolve_to("93.184.216.34")
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/hook", secret={"secret": "s"})
    api.add("POST", PINNED, status=204)
    r = staff.post(f"/studio/webhooks/{hook.pk}/test/")
    assert r.status_code == 302 and r["Location"] == "/studio/webhooks/"
    assert len(api.calls("POST", "93.184.216.34")) == 1
    assert "“n8n” answered 204." in html(staff.get("/studio/webhooks/"))


def test_send_test_shows_the_error_sentence(staff, api, resolve_to):
    resolve_to("93.184.216.34")
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/hook", secret={"secret": "s"})
    api.add("POST", PINNED, status=404)
    page = html(staff.post(f"/studio/webhooks/{hook.pk}/test/", follow=True))
    assert "Webhook “n8n” answered 404. Check the URL and the receiving workflow." in page
    assert 'at-note--danger' in page


def test_delete_a_hook(staff):
    hook = OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/hook", secret={"secret": "s"})
    r = staff.post(f"/studio/webhooks/{hook.pk}/delete/")
    assert r.status_code == 302 and r["Location"] == "/studio/webhooks/"
    assert not OutboundHook.objects.exists()


def test_missing_hook_is_404(staff):
    assert staff.get("/studio/webhooks/999/").status_code == 404
    assert staff.post("/studio/webhooks/999/test/").status_code == 404
