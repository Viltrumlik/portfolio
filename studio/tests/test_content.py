"""Content: profile, experience / skills / services / links, posts (publishing emits once), project curation."""
import datetime as dt

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from automations.models import Event
from content.models import Experience, Post, Profile, Project, Service, Skill, SocialLink, Tag
from jobs.models import Job

pytestmark = pytest.mark.django_db

PROFILE = {
    "name": "Alisher Muhammadaliyev", "handle": "alisher.os", "headline": "I build backends that keep working",
    "bio": "I build **bots**.", "location": "Fergana, Uzbekistan", "timezone": "Asia/Tashkent", "email": "me@example.com",
    "availability": "busy", "availability_note": "Booked until March",
}


def html(response, status=200):
    assert response.status_code == status, response.status_code
    return response.content.decode()


# --- profile --------------------------------------------------------------------------


def test_content_index_shows_the_profile_form_and_sections(staff):
    page = html(staff.get("/studio/content/"))
    for name in ("name", "headline", "bio", "availability", "availability_note", "timezone"):
        assert f'name="{name}"' in page
    for href in ("/studio/content/experience/", "/studio/content/skills/", "/studio/content/services/",
                 "/studio/content/links/", "/studio/content/posts/", "/studio/content/projects/"):
        assert f'href="{href}"' in page


def test_save_the_profile(staff):
    r = staff.post("/studio/content/", PROFILE)
    assert r.status_code == 302 and r["Location"] == "/studio/content/"
    p = Profile.load()
    assert (p.headline, p.availability, p.availability_note, p.timezone) == (
        "I build backends that keep working", "busy", "Booked until March", "Asia/Tashkent")
    assert "Profile saved" in html(staff.get("/studio/content/"))


def test_profile_rejects_an_unknown_timezone(staff):
    page = html(staff.post("/studio/content/", {**PROFILE, "timezone": "Mars/Olympus"}))
    assert "Use a time zone name such as Asia/Tashkent." in page
    assert Profile.load().timezone != "Mars/Olympus"


# --- simple collections ---------------------------------------------------------------


def test_create_edit_and_delete_experience(staff):
    r = staff.post("/studio/content/experience/new/", {
        "company": "Acme", "role": "Backend developer", "description": "APIs", "location": "Remote",
        "start_date": "2023-01-01", "end_date": "", "order": 0,
    })
    assert r.status_code == 302 and r["Location"] == "/studio/content/experience/"
    job = Experience.objects.get()
    assert (job.company, job.start_date, job.end_date) == ("Acme", dt.date(2023, 1, 1), None)
    assert "Backend developer" in html(staff.get("/studio/content/experience/"))

    staff.post(f"/studio/content/experience/{job.pk}/", {"company": "Acme", "role": "Lead", "start_date": "2023-01-01", "end_date": "2024-06-30", "order": 1})
    job.refresh_from_db()
    assert (job.role, job.end_date) == ("Lead", dt.date(2024, 6, 30))

    r = staff.post(f"/studio/content/experience/{job.pk}/delete/")
    assert r.status_code == 302 and not Experience.objects.exists()


def test_experience_end_cannot_precede_start(staff):
    page = html(staff.post("/studio/content/experience/new/", {"company": "Acme", "role": "Dev", "start_date": "2024-01-01", "end_date": "2023-01-01", "order": 0}))
    assert "The end date is before the start date." in page
    assert not Experience.objects.exists()


def test_create_skill_service_and_link(staff):
    assert staff.post("/studio/content/skills/new/", {"name": "Django", "group": "Backend", "order": 1}).status_code == 302
    assert staff.post("/studio/content/services/new/", {"title": "APIs", "description": "REST and webhooks.", "order": 0}).status_code == 302
    assert staff.post("/studio/content/links/new/", {"platform": "github", "label": "GitHub", "url": "https://github.com/a1", "order": 0}).status_code == 302
    assert Skill.objects.get().group == "Backend"
    assert Service.objects.get().title == "APIs"
    assert SocialLink.objects.get().url == "https://github.com/a1"


def test_links_need_a_valid_url(staff):
    page = html(staff.post("/studio/content/links/new/", {"platform": "github", "url": "not a url", "order": 0}))
    assert "at-field--error" in page
    assert not SocialLink.objects.exists()


def test_unknown_collection_is_404(staff):
    assert staff.get("/studio/content/widgets/").status_code == 404
    assert staff.post("/studio/content/posts/1/delete/").status_code == 404


# --- posts ----------------------------------------------------------------------------


def post_data(**fields):
    return {"title": "Notes from building things", "slug": "", "excerpt": "Short.", "body": "# Hello\n\nMarkdown **body**.",
            "tags": "Django, Bots", "status": "draft", **fields}


def test_create_a_draft_post_with_tags_and_a_generated_slug(staff):
    r = staff.post("/studio/content/posts/new/", post_data())
    post = Post.objects.get()
    assert r.status_code == 302 and r["Location"] == f"/studio/content/posts/{post.pk}/"
    assert post.slug == "notes-from-building-things"
    assert post.status == "draft" and post.published_at is None
    assert sorted(t.name for t in post.tags.all()) == ["Bots", "Django"]
    assert not Event.objects.filter(type="post.published").exists()


def test_publishing_sets_published_at_and_emits_exactly_once(staff):
    staff.post("/studio/content/posts/new/", post_data())
    post = Post.objects.get()
    staff.post(f"/studio/content/posts/{post.pk}/", post_data(slug=post.slug, status="published"))
    post.refresh_from_db()
    assert post.status == "published" and post.published_at is not None
    events = Event.objects.filter(type="post.published")
    assert events.count() == 1
    event = events.get()
    assert event.payload == {"title": "Notes from building things", "url": "https://guts.test/writing/notes-from-building-things/"}
    assert (event.source, event.public) == ("site", True)
    assert Job.objects.filter(kind="automations.dispatch", payload={"event_id": event.pk}).count() == 1
    # Saving again, or unpublishing and republishing, does not announce it twice.
    first = post.published_at
    staff.post(f"/studio/content/posts/{post.pk}/", post_data(slug=post.slug, status="published", title="Renamed"))
    staff.post(f"/studio/content/posts/{post.pk}/", post_data(slug=post.slug, status="draft"))
    staff.post(f"/studio/content/posts/{post.pk}/", post_data(slug=post.slug, status="published"))
    post.refresh_from_db()
    assert post.published_at == first
    assert Event.objects.filter(type="post.published").count() == 1


def test_creating_a_post_as_published_emits_once(staff):
    staff.post("/studio/content/posts/new/", post_data(status="published", slug="hello"))
    assert Event.objects.filter(type="post.published").count() == 1
    assert Post.objects.get().published_at is not None


def test_duplicate_slug_is_refused(staff):
    Post.objects.create(title="Hello", slug="hello")
    page = html(staff.post("/studio/content/posts/new/", post_data(slug="hello")))
    assert "already" in page
    assert Post.objects.count() == 1


def test_post_list_shows_status(staff):
    Post.objects.create(title="Draft one", slug="draft-one")
    Post.objects.create(title="Live one", slug="live-one", status="published", published_at=timezone.now())
    page = html(staff.get("/studio/content/posts/"))
    assert "Draft one" in page and "Live one" in page and "Draft" in page and "Published" in page
    assert 'href="/studio/content/posts/new/"' in page


def test_post_body_is_a_markdown_textarea(staff):
    page = html(staff.get("/studio/content/posts/new/"))
    assert '<textarea name="body"' in page
    assert 'name="slug"' in page and 'name="tags"' in page and 'name="status"' in page


# --- projects -------------------------------------------------------------------------


def test_project_curation(staff):
    project = Project.objects.create(repo_full_name="a1/volunteers_bot", slug="volunteers-bot")
    page = html(staff.get("/studio/content/projects/"))
    assert "volunteers_bot" in page and f'href="/studio/content/projects/{project.pk}/"' in page
    r = staff.post(f"/studio/content/projects/{project.pk}/", {
        "title": "Volunteers bot", "summary": "Matches volunteers to shifts.", "kind": "Bot",
        "case_study": "## Why\nBecause.", "stack": "Python, aiogram, PostgreSQL", "featured": "on", "order": 2,
    })
    assert r.status_code == 302 and r["Location"] == "/studio/content/projects/"
    project.refresh_from_db()
    assert (project.title, project.kind, project.featured, project.hidden, project.order) == ("Volunteers bot", "Bot", True, False, 2)
    assert project.stack == ["Python", "aiogram", "PostgreSQL"]
    assert project.case_study == "## Why\nBecause."
    assert project.repo_full_name == "a1/volunteers_bot"


def test_project_edit_shows_stack_as_text(staff):
    project = Project.objects.create(repo_full_name="a1/bot", slug="bot", stack=["Python", "Django"])
    page = html(staff.get(f"/studio/content/projects/{project.pk}/"))
    assert 'value="Python, Django"' in page


def test_tags_are_reused(staff):
    Tag.objects.create(name="Django", slug="django")
    staff.post("/studio/content/posts/new/", post_data(tags="django, New tag"))
    assert sorted(Tag.objects.values_list("slug", flat=True)) == ["django", "new-tag"]


# --- images ---------------------------------------------------------------------------


def png(name="shot.png"):
    buf = io.BytesIO()
    Image.new("RGB", (12, 8), (0, 255, 65)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_project_form_uploads_an_image(staff):
    project = Project.objects.create(repo_full_name="a1/mars", slug="mars")
    page = html(staff.get(f"/studio/content/projects/{project.pk}/"))
    assert 'enctype="multipart/form-data"' in page and 'name="image"' in page
    r = staff.post(f"/studio/content/projects/{project.pk}/", {"title": "Mars", "stack": "", "order": 0, "image": png()})
    assert r.status_code == 302
    project.refresh_from_db()
    assert project.image.name.startswith("projects/shot")


def test_project_form_rejects_a_file_that_is_not_an_image(staff):
    project = Project.objects.create(repo_full_name="a1/mars", slug="mars")
    fake = SimpleUploadedFile("shot.png", b"not an image", content_type="image/png")
    r = staff.post(f"/studio/content/projects/{project.pk}/", {"title": "Mars", "stack": "", "order": 0, "image": fake})
    assert r.status_code == 200
    project.refresh_from_db()
    assert not project.image


def test_post_form_uploads_a_cover(staff):
    r = staff.post("/studio/content/posts/new/", {**post_data(), "cover": png("cover.png")})
    assert r.status_code == 302
    assert Post.objects.get().cover.name.startswith("writing/cover")
