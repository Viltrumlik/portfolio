import datetime as dt
import json
import re

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from automations.models import Event
from content.models import Experience, Post, Service, Skill
from integrations.models import ContributionDay

from . import factories as f

pytestmark = pytest.mark.django_db


def html_of(response, keep_cmdk=False):
    """The page HTML; by default without the ⌘K JSON, which lists every page, project and post."""
    assert response.status_code == 200, response.status_code
    html = response.content.decode()
    if keep_cmdk:
        return html
    return re.sub(r'<script id="atlas-cmdk" type="application/json">.*?</script>', "", html, flags=re.S)


# home ------------------------------------------------------------------------------------


def test_home_renders_menubar_desk_about_now_and_dock(client):
    f.profile()
    html = html_of(client.get("/"))
    assert '<header class="at-menubar">' in html
    assert '<div class="at-desk" data-island="desk" style="--desk-h:560px">' in html
    assert '<section class="at-win is-active" data-win="about" aria-label="about.md"' in html
    assert "I build backends that keep working" in html
    assert "I build server-side systems, REST APIs and bots." in html
    assert '<a href="/work/" class="at-btn at-btn--primary"><span>See my work</span>' in html
    assert 'data-island="now" data-src="/api/live/now.json"' in html
    assert '<nav class="at-dock" aria-label="Dock">' in html
    assert 'href="/writing/feed.xml" class="at-dock__item"' in html
    assert 'href="/contact/" class="at-dock__item"' in html


def test_home_hides_github_window_and_dock_item_without_data(client):
    f.profile()
    html = html_of(client.get("/"))
    assert "github.app" not in html
    assert ">GH</a>" not in html


def test_home_shows_github_window_when_contributions_exist(client):
    f.profile()
    ContributionDay.objects.create(date=dt.date(2026, 11, 10), count=4)
    html = html_of(client.get("/"))
    assert 'aria-label="github.app"' in html
    assert '<figure class="at-graph">' in html
    assert '>GH</a>' in html


def test_home_selected_work_lists_featured_visible_projects(client):
    f.profile()
    f.project("volunteers-bot", featured=True, kind="Bot")
    f.project("secret", featured=True, hidden=True)
    f.project("side-thing")
    html = html_of(client.get("/"))
    assert "01" in html and "Selected work" in html
    assert 'href="/work/volunteers-bot/"' in html
    assert "/work/secret/" not in html
    assert "/work/side-thing/" not in html


def test_home_writing_shows_latest_three_published(client):
    f.profile()
    for i in range(4):
        f.post(f"post-{i}", days_ago=i + 1)
    f.post("draft-post", status=Post.Status.DRAFT)
    html = html_of(client.get("/"))
    assert "/writing/post-0/" in html and "/writing/post-2/" in html
    assert "/writing/post-3/" not in html
    assert "draft-post" not in html


def test_home_activity_section_only_with_data(client):
    f.profile()
    html = html_of(client.get("/"))
    assert "activity.log" not in html
    f.repo("shop", pinned=True, description="A shop.")
    f.repo("unpinned")
    Event.objects.create(type="github.push", source="github", public=True, payload={"repo": "a1/shop", "commits": 2})
    Event.objects.create(type="contact.submitted", source="site", public=False, payload={"name": "Secret"})
    html = html_of(client.get("/"))
    assert 'aria-label="activity.log"' in html
    assert '<a class="at-repo" href="https://github.com/a1/shop">' in html
    assert "a1/unpinned" not in html and ">unpinned<" not in html
    assert "Pushed 2 commits to a1/shop" in html
    assert "Secret" not in html


def test_section_indexes_follow_page_order(client):
    f.profile()
    f.project("p1", featured=True)
    f.post("hello")
    html = html_of(client.get("/"))
    indexes = re.findall(r'<span class="at-section__index">(\d\d)</span>', html)
    assert indexes == ["01", "02", "03"]  # work, writing, contact (no activity data)


def test_home_contact_window_has_form(client):
    f.profile()
    html = html_of(client.get("/"))
    assert '<form method="post" action="/contact/"' in html
    assert 'name="website"' in html


# command palette -------------------------------------------------------------------------


def _cmdk(html):
    m = re.search(r'<script id="atlas-cmdk" type="application/json">(.*?)</script>', html, re.S)
    assert m, "missing atlas-cmdk data"
    return json.loads(m.group(1))


def test_command_palette_data_for_visitors(client):
    f.profile(email="me@example.com")
    f.project("visible-one")
    f.project("hidden-one", hidden=True)
    f.post("a-post")
    data = _cmdk(html_of(client.get("/about/"), keep_cmdk=True))
    labels = [g["label"] for g in data["groups"]]
    assert labels == ["Pages", "Projects", "Writing", "Actions"]
    projects = [i["href"] for i in data["groups"][1]["items"]]
    assert projects == ["/work/visible-one/"]
    actions = data["groups"][-1]["items"]
    assert {"label": "Switch theme", "action": "theme", "icon": "power"}.items() <= actions[0].items()
    assert any(a["action"] == "copy:me@example.com" and a["icon"] == "link" for a in actions if "action" in a)
    assert not any(a.get("href") == "/studio/" for a in actions)


def test_command_palette_offers_studio_to_staff(client):
    f.profile()
    staff = get_user_model().objects.create_user("owner", password="x-test-pass", is_staff=True)
    client.force_login(staff)
    data = _cmdk(html_of(client.get("/"), keep_cmdk=True))
    assert any(a.get("href") == "/studio/" and a["label"] == "Open studio" for a in data["groups"][-1]["items"])


# work ------------------------------------------------------------------------------------


def test_work_lists_visible_projects_and_filters_by_language(client):
    f.profile()
    f.project("py-thing", repo=f.repo("py-thing", language="Python"))
    f.project("ts-thing", repo=f.repo("ts-thing", language="TypeScript"))
    f.project("kotlin-app", stack=["Kotlin", "Flutter"])
    f.project("hidden", hidden=True)
    html = html_of(client.get("/work/"))
    for slug in ("py-thing", "ts-thing", "kotlin-app"):
        assert f"/work/{slug}/" in html
    assert "/work/hidden/" not in html
    assert 'href="?lang=Python"' in html
    html = html_of(client.get("/work/?lang=python"))
    assert "/work/py-thing/" in html and "/work/ts-thing/" not in html
    html = html_of(client.get("/work/?lang=Kotlin"))
    assert "/work/kotlin-app/" in html and "/work/py-thing/" not in html


def test_project_case_study(client):
    f.profile()
    repo = f.repo("volunteers_bot", stars=12, forks=3, homepage="https://bot.example.com",
                  pushed_at=timezone.now() - dt.timedelta(days=3))
    f.project("volunteers-bot", repo=repo, title="Volunteers bot", summary="Registers volunteers.",
              case_study="## Why\n\nIt **works**.<script>alert(1)</script>", stack=["aiogram"])
    html = html_of(client.get("/work/volunteers-bot/"))
    assert "<h2>Why</h2>" in html and "<strong>works</strong>" in html
    assert "<script>alert(1)</script>" not in html
    assert '<div class="at-stat__value">12</div>' in html
    assert 'href="https://github.com/a1/volunteers_bot"' in html
    assert 'href="https://bot.example.com"' in html
    assert "aiogram" in html


def test_hidden_or_missing_project_is_404(client):
    f.profile()
    f.project("nope", hidden=True)
    assert client.get("/work/nope/").status_code == 404
    assert client.get("/work/missing/").status_code == 404


# writing ---------------------------------------------------------------------------------


def test_writing_list_shows_published_only(client):
    f.profile()
    f.post("live-post", tags=["Django"])
    f.post("draft", status=Post.Status.DRAFT)
    f.post("future", days_ago=-3)
    html = html_of(client.get("/writing/"))
    assert "/writing/live-post/" in html
    assert "/writing/draft/" not in html and "/writing/future/" not in html
    assert 'href="/writing/tag/django/"' in html


def test_post_detail_markdown_and_migrated_html(client):
    f.profile()
    f.post("md", body="## Heading\n\nSome *text*.")
    f.post("legacy", body='<h2>Old</h2><p onclick="x()">Hi</p><script>evil()</script>', body_format=Post.Format.HTML)
    html = html_of(client.get("/writing/md/"))
    assert "<h2>Heading</h2>" in html and "<em>text</em>" in html
    html = html_of(client.get("/writing/legacy/"))
    assert "<h2>Old</h2><p>Hi</p>" in html
    assert "evil()" not in html and "onclick" not in html


def test_draft_and_future_posts_are_404(client):
    f.profile()
    f.post("draft", status=Post.Status.DRAFT)
    f.post("future", days_ago=-2)
    assert client.get("/writing/draft/").status_code == 404
    assert client.get("/writing/future/").status_code == 404


def test_tag_page(client):
    f.profile()
    f.post("tagged", tags=["Python"])
    f.post("other", tags=["Go"])
    html = html_of(client.get("/writing/tag/python/"))
    assert "/writing/tagged/" in html and "/writing/other/" not in html
    assert client.get("/writing/tag/unknown/").status_code == 404


# about -----------------------------------------------------------------------------------


def test_about_page(client):
    f.profile(bio="I build **APIs**.\n\nAnd bots.")
    Experience.objects.create(company="Najot Ta'lim", role="Backend student", start_date=dt.date(2024, 9, 1))
    Skill.objects.create(name="Django", group="Backend")
    Skill.objects.create(name="PostgreSQL", group="Databases")
    Service.objects.create(title="REST API development", description="APIs.\n\n- JWT auth")
    html = html_of(client.get("/about/"))
    assert "<strong>APIs</strong>" in html
    assert "Najot Ta&#x27;lim" in html and "Backend student" in html and "Present" in html
    assert "Backend" in html and "Django" in html and "Databases" in html
    assert "REST API development" in html and "<li>JWT auth</li>" in html
    assert "Download CV" not in html


def test_about_links_cv_when_uploaded(client):
    f.profile(cv="cv/alisher.pdf")
    html = html_of(client.get("/about/"))
    assert "Download CV" in html and "/media/cv/alisher.pdf" in html


# errors ----------------------------------------------------------------------------------


def test_404_is_an_error_window(client):
    f.profile()
    r = client.get("/definitely-not-here/")
    assert r.status_code == 404
    html = r.content.decode()
    assert 'class="at-win' in html and "404" in html
    assert 'href="/"' in html
