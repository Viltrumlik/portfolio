"""Who may open the studio: anonymous visitors are sent to log in, non-staff get 403, the owner gets in."""
import datetime as dt

import pytest
from django.test import Client
from django.urls import URLPattern, resolve
from django.utils import timezone

from automations.models import Rule
from content.models import Experience, Post, Project, Service, Skill, SocialLink
from integrations.models import OutboundHook
from jobs.models import Job
from studio import urls as studio_urls
from web.models import ContactMessage

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

PAGES = [
    "/studio/",
    "/studio/connections/github/",
    "/studio/connections/telegram/",
    "/studio/connections/lastfm/",
    "/studio/connections/github/disconnect/",
    "/studio/webhooks/",
    "/studio/webhooks/{hook}/",
    "/studio/automations/",
    "/studio/automations/new/",
    "/studio/automations/{rule}/",
    "/studio/content/",
    "/studio/content/experience/",
    "/studio/content/experience/new/",
    "/studio/content/experience/{experience}/",
    "/studio/content/skills/",
    "/studio/content/skills/new/",
    "/studio/content/skills/{skill}/",
    "/studio/content/services/",
    "/studio/content/services/new/",
    "/studio/content/services/{service}/",
    "/studio/content/links/",
    "/studio/content/links/new/",
    "/studio/content/links/{link}/",
    "/studio/content/posts/",
    "/studio/content/posts/new/",
    "/studio/content/posts/{post}/",
    "/studio/content/projects/",
    "/studio/content/projects/{project}/",
    "/studio/inbox/",
    "/studio/jobs/",
]

ACTIONS = [
    "/studio/connections/github/sync/",
    "/studio/connections/telegram/verify/",
    "/studio/webhooks/{hook}/test/",
    "/studio/webhooks/{hook}/delete/",
    "/studio/automations/{rule}/toggle/",
    "/studio/automations/{rule}/delete/",
    "/studio/content/experience/{experience}/delete/",
    "/studio/content/skills/{skill}/delete/",
    "/studio/content/services/{service}/delete/",
    "/studio/content/links/{link}/delete/",
    "/studio/inbox/{message}/read/",
    "/studio/inbox/{message}/delete/",
    "/studio/jobs/{job}/retry/",
]


@pytest.fixture
def ids():
    return {
        "hook": OutboundHook.objects.create(name="n8n", url="https://n8n.example.com/h", secret={"secret": "s"}).pk,
        "rule": Rule.objects.create(name="Mine", trigger="post.published", action="telegram.send", action_config={"template": "x"}).pk,
        "experience": Experience.objects.create(company="Acme", role="Backend developer", start_date=dt.date(2023, 1, 1)).pk,
        "skill": Skill.objects.create(name="Django").pk,
        "service": Service.objects.create(title="APIs").pk,
        "link": SocialLink.objects.create(platform="github", url="https://github.com/a1").pk,
        "post": Post.objects.create(title="Hello", slug="hello").pk,
        "project": Project.objects.create(repo_full_name="a1/bot", slug="bot").pk,
        "message": ContactMessage.objects.create(name="Dana", email="dana@example.com", message="Hi").pk,
        "job": Job.objects.create(kind="github.sync", status=Job.Status.FAILED, finished_at=timezone.now()).pk,
    }


def _all(ids, routes):
    return [r.format(**ids) for r in routes]


def test_the_route_lists_cover_every_studio_url(ids):
    covered = {resolve(url).url_name for url in _all(ids, PAGES + ACTIONS)}
    names = {p.name for p in studio_urls.urlpatterns if isinstance(p, URLPattern)}
    assert names - covered == {"login", "logout"}


def test_anonymous_visitors_are_sent_to_log_in(client, ids):
    for url in _all(ids, PAGES + ACTIONS):
        for method in (client.get, client.post):
            r = method(url)
            assert r.status_code == 302, (method.__name__, url, r.status_code)
            assert r["Location"].startswith("/studio/login/?next="), url


def test_non_staff_users_are_forbidden(client, member, ids):
    client.force_login(member)
    for url in _all(ids, PAGES + ACTIONS):
        assert client.get(url).status_code == 403, url
        assert client.post(url).status_code == 403, url


def test_the_owner_can_open_every_page(staff, ids):
    for url in _all(ids, PAGES):
        r = staff.get(url)
        assert r.status_code == 200, (url, r.status_code)
        assert r["Cache-Control"].startswith("max-age=0") or "no-cache" in r["Cache-Control"], url


def test_actions_refuse_get(staff, ids):
    for url in _all(ids, ACTIONS):
        assert staff.get(url).status_code == 405, url
    assert Job.objects.get(pk=ids["job"]).status == Job.Status.FAILED
    assert ContactMessage.objects.get(pk=ids["message"]).is_read is False


def test_unknown_provider_is_404(staff):
    assert staff.get("/studio/connections/myspace/").status_code == 404
    assert staff.post("/studio/connections/myspace/sync/").status_code == 404


def test_mutations_need_a_csrf_token(owner, ids):
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    assert client.post(f"/studio/inbox/{ids['message']}/read/").status_code == 403
    assert ContactMessage.objects.get(pk=ids["message"]).is_read is False


def test_studio_pages_are_noindex_and_carry_the_studio_menubar(staff):
    html = staff.get("/studio/").content.decode()
    assert '<meta name="robots" content="noindex, nofollow">' in html
    assert 'aria-label="Studio"' in html
    for label in ("Desk", "Automations", "Content", "Inbox", "Jobs", "View site", "Log out"):
        assert f">{label}<" in html, label
    assert 'action="/studio/logout/"' in html


# --- login / logout ------------------------------------------------------------------


def test_login_page_uses_atlas_fields(client):
    html = client.get("/studio/login/").content.decode()
    assert 'class="at-field"' in html and 'class="at-field__input"' in html
    assert 'name="username"' in html and 'type="password"' in html
    assert "csrfmiddlewaretoken" in html


def test_owner_logs_in_and_lands_on_the_desk(client, owner):
    r = client.post("/studio/login/", {"username": "owner", "password": PASSWORD})
    assert r.status_code == 302 and r["Location"] == "/studio/"
    assert client.get("/studio/").status_code == 200


def test_login_follows_next(client, owner):
    r = client.post("/studio/login/?next=/studio/inbox/", {"username": "owner", "password": PASSWORD})
    assert r["Location"] == "/studio/inbox/"


def test_wrong_password_says_so(client, owner):
    r = client.post("/studio/login/", {"username": "owner", "password": "nope"})
    assert r.status_code == 200
    assert "username and password don" in r.content.decode()
    assert "_auth_user_id" not in client.session


def test_non_staff_accounts_cannot_log_in(client, member):
    r = client.post("/studio/login/", {"username": "member", "password": PASSWORD})
    assert r.status_code == 200
    assert "can’t open the studio" in r.content.decode()
    assert "_auth_user_id" not in client.session


def test_five_failed_logins_lock_the_ip_for_15_minutes(client, owner):
    for _ in range(5):
        assert client.post("/studio/login/", {"username": "owner", "password": "nope"}, HTTP_X_REAL_IP="198.51.100.7").status_code == 200
    r = client.post("/studio/login/", {"username": "owner", "password": PASSWORD}, HTTP_X_REAL_IP="198.51.100.7")
    assert r.status_code == 429
    assert "Too many failed sign-ins" in r.content.decode()
    assert "_auth_user_id" not in client.session
    # Another address is not affected.
    r = client.post("/studio/login/", {"username": "owner", "password": PASSWORD}, HTTP_X_REAL_IP="198.51.100.8")
    assert r.status_code == 302


def test_rate_limit_falls_back_to_remote_addr(client, owner):
    for _ in range(5):
        client.post("/studio/login/", {"username": "owner", "password": "nope"}, REMOTE_ADDR="203.0.113.5")
    assert client.post("/studio/login/", {"username": "owner", "password": PASSWORD}, REMOTE_ADDR="203.0.113.5").status_code == 429
    assert client.post("/studio/login/", {"username": "owner", "password": PASSWORD}, REMOTE_ADDR="203.0.113.6").status_code == 302


def test_failures_are_counted_in_a_15_minute_window(client, owner, monkeypatch):
    from studio import auth

    windows = []
    real_add = auth.cache.add
    monkeypatch.setattr(auth.cache, "add", lambda key, value, timeout=None: windows.append(timeout) or real_add(key, value, timeout))
    client.post("/studio/login/", {"username": "owner", "password": "nope"}, REMOTE_ADDR="203.0.113.5")
    assert windows == [15 * 60]


def test_a_successful_login_clears_the_failures(client, owner):
    for _ in range(4):
        client.post("/studio/login/", {"username": "owner", "password": "nope"}, REMOTE_ADDR="203.0.113.5")
    assert client.post("/studio/login/", {"username": "owner", "password": PASSWORD}, REMOTE_ADDR="203.0.113.5").status_code == 302
    client.logout()
    for _ in range(4):
        client.post("/studio/login/", {"username": "owner", "password": "nope"}, REMOTE_ADDR="203.0.113.5")
    assert client.post("/studio/login/", {"username": "owner", "password": PASSWORD}, REMOTE_ADDR="203.0.113.5").status_code == 302


def test_logout_is_post_only(staff):
    assert staff.get("/studio/logout/").status_code == 405
    r = staff.post("/studio/logout/")
    assert r.status_code == 302 and r["Location"] == "/"
    assert staff.get("/studio/").status_code == 302
