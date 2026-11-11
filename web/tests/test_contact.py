import hashlib

import pytest
from django.conf import settings

from automations.models import Event
from web.models import ContactMessage

from . import factories as f

pytestmark = pytest.mark.django_db

GOOD = {"name": "Dana", "email": "dana@example.com", "message": "Can you build me an API?", "website": ""}


@pytest.fixture(autouse=True)
def _profile():
    f.profile()


def test_get_renders_form_with_hidden_honeypot(client):
    r = client.get("/contact/")
    html = r.content.decode()
    assert r.status_code == 200
    for field in ("name", "email", "message"):
        assert f'name="{field}"' in html
    assert 'name="website"' in html and 'tabindex="-1"' in html and 'autocomplete="off"' in html
    assert 'aria-label="contact.md"' in html


def test_valid_post_saves_emits_and_redirects_with_message(client):
    r = client.post("/contact/", GOOD, REMOTE_ADDR="203.0.113.9")
    assert r.status_code == 302 and r["Location"] == "/contact/"
    msg = ContactMessage.objects.get()
    assert (msg.name, msg.email, msg.message) == ("Dana", "dana@example.com", "Can you build me an API?")
    assert len(msg.ip_hash) == 64 and "203.0.113.9" not in msg.ip_hash
    assert msg.ip_hash == hashlib.sha256(f"{settings.SECRET_KEY}:203.0.113.9".encode()).hexdigest()
    event = Event.objects.get(type="contact.submitted")
    assert event.source == "site" and event.public is False
    assert event.payload == {"id": msg.pk, "name": "Dana", "email": "dana@example.com", "message": "Can you build me an API?"}
    page = client.get("/contact/").content.decode()
    assert "Thanks, Dana" in page


def test_invalid_post_shows_errors_and_saves_nothing(client):
    r = client.post("/contact/", {**GOOD, "email": "not-an-email"})
    assert r.status_code == 200
    assert "at-field--error" in r.content.decode()
    assert ContactMessage.objects.count() == 0
    assert not Event.objects.exists()


def test_honeypot_looks_like_success_but_drops_the_message(client):
    r = client.post("/contact/", {**GOOD, "website": "http://spam.example"})
    assert r.status_code == 302
    assert ContactMessage.objects.count() == 0
    assert not Event.objects.exists()


def test_rate_limit_is_five_per_hour_per_ip(client):
    for _ in range(5):
        assert client.post("/contact/", GOOD, REMOTE_ADDR="198.51.100.7").status_code == 302
    r = client.post("/contact/", GOOD, REMOTE_ADDR="198.51.100.7")
    assert r.status_code == 429
    assert "Too many messages" in r.content.decode()
    assert ContactMessage.objects.count() == 5
    assert client.post("/contact/", GOOD, REMOTE_ADDR="198.51.100.8").status_code == 302


def test_client_ip_comes_from_proxy_header(client):
    client.post("/contact/", GOOD, REMOTE_ADDR="", HTTP_X_REAL_IP="192.0.2.44")
    expected = hashlib.sha256(f"{settings.SECRET_KEY}:192.0.2.44".encode()).hexdigest()
    assert ContactMessage.objects.get().ip_hash == expected
