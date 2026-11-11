"""import_legacy reads the old site's tables from a separate SQLite file. The fixture below recreates
those tables with the same columns as the production database (never the real db.sqlite3)."""
import datetime as dt
import sqlite3
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from content.models import Experience, Post, Profile, Project, Service, Skill, SocialLink, Tag
from integrations.models import Repo
from web.models import ContactMessage

pytestmark = pytest.mark.django_db

LEGACY_SCHEMA = """
CREATE TABLE "core_sitesetting" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "hero_title" varchar(500) NOT NULL, "hero_subtitle" varchar(500) NOT NULL, "contact_email" varchar(254) NOT NULL, "logo" varchar(100) NULL, "favicon" varchar(100) NULL, "hero_description" text NOT NULL, "hero_greeting" varchar(100) NOT NULL, "cv" varchar(100) NULL, "location" varchar(200) NOT NULL, "phone" varchar(50) NOT NULL, "site_name" varchar(200) NOT NULL);
CREATE TABLE "core_sociallink" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "platform_name" varchar(50) NOT NULL, "url" varchar(200) NOT NULL, "icon_class" varchar(100) NOT NULL, "order" integer unsigned NOT NULL, "is_active" bool NOT NULL);
CREATE TABLE "core_contactmessage" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(200) NOT NULL, "email" varchar(254) NOT NULL, "subject" varchar(255) NOT NULL, "message" text NOT NULL, "created_at" datetime NOT NULL, "is_read" bool NOT NULL, "emailed" bool NOT NULL);
CREATE TABLE "pages_aboutsection" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "content" text NOT NULL, "education" varchar(200) NOT NULL, "location" varchar(200) NOT NULL, "projects_completed" varchar(50) NOT NULL, "happy_clients" varchar(50) NOT NULL, "languages" varchar(200) NOT NULL, "years_experience" varchar(50) NOT NULL);
CREATE TABLE "pages_experience" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "company" varchar(200) NOT NULL, "role" varchar(200) NOT NULL, "description" text NOT NULL, "start_date" date NOT NULL, "end_date" date NULL, "is_current" bool NOT NULL, "order" integer unsigned NOT NULL);
CREATE TABLE "pages_skill" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "level" integer unsigned NOT NULL, "group" varchar(20) NOT NULL, "icon_class" varchar(100) NOT NULL, "order" integer unsigned NOT NULL);
CREATE TABLE "pages_service" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "description" text NOT NULL, "icon_class" varchar(100) NOT NULL, "order" integer unsigned NOT NULL);
CREATE TABLE "pages_servicefeature" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "service_id" bigint NOT NULL);
CREATE TABLE "blog_category" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL UNIQUE, "slug" varchar(120) NOT NULL UNIQUE, "description" text NOT NULL);
CREATE TABLE "blog_tag" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(50) NOT NULL UNIQUE, "slug" varchar(60) NOT NULL UNIQUE);
CREATE TABLE "blog_article" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "slug" varchar(250) NOT NULL UNIQUE, "excerpt" text NOT NULL, "content" text NOT NULL, "published" bool NOT NULL, "published_at" datetime NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "reading_time" integer unsigned NOT NULL, "category_id" bigint NOT NULL, "cover" varchar(100) NULL);
CREATE TABLE "blog_article_tags" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "article_id" bigint NOT NULL, "tag_id" bigint NOT NULL);
CREATE TABLE "portfolio_project" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "slug" varchar(250) NOT NULL UNIQUE, "short_description" text NOT NULL, "description" text NOT NULL, "github_url" varchar(200) NULL, "live_url" varchar(200) NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "is_featured" bool NOT NULL, "is_active" bool NOT NULL, "image" varchar(100) NULL);
CREATE TABLE "portfolio_technology" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL UNIQUE, "icon_class" varchar(100) NOT NULL, "slug" varchar(120) NOT NULL UNIQUE);
CREATE TABLE "portfolio_project_technologies" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "project_id" bigint NOT NULL, "technology_id" bigint NOT NULL);
"""

ROWS = [
    ("INSERT INTO core_sitesetting VALUES (1, ?, ?, ?, '', '', ?, '👋 Hello', '', ?, '', ?)",
     ("I'm Alisher M", "Backend Developer & Software Engineer", "alisher@example.com",
      "I build reliable backends.", "Fergana, Uzbekistan", "Alisher M")),
    ("INSERT INTO pages_aboutsection VALUES (1, 'About Me', ?, '', 'Fergana', '', '', '', '')",
     ("<p>I'm Alisher, a backend developer.</p><p>I build <strong>APIs</strong> &amp; bots.</p>",)),
    ("INSERT INTO core_sociallink VALUES (1, 'github', 'https://github.com/A1isherDev', 'fab fa-github', 1, 1)", ()),
    ("INSERT INTO core_sociallink VALUES (2, 'telegram', 'https://t.me/alisher', 'fab fa-telegram', 2, 1)", ()),
    ("INSERT INTO core_sociallink VALUES (3, 'facebook', 'https://facebook.com/x', 'fab fa-facebook', 3, 0)", ()),
    ("INSERT INTO pages_experience VALUES (1, 'Najot Ta''lim', 'Backend student', 'Studying Django.', '2024-09-01', NULL, 1, 1)", ()),
    ("INSERT INTO pages_experience VALUES (2, 'Acme', 'Intern', 'Fixed bugs.', '2023-01-01', '2023-06-30', 0, 2)", ()),
    ("INSERT INTO pages_skill VALUES (1, 'Python', 90, 'backend', 'x', 1)", ()),
    ("INSERT INTO pages_skill VALUES (2, 'PostgreSQL', 80, 'database', 'x', 2)", ()),
    ("INSERT INTO pages_skill VALUES (3, 'Docker', 72, 'devops', 'x', 3)", ()),
    ("INSERT INTO pages_service VALUES (1, 'REST API Development', 'Secure REST APIs.', 'x', 1)", ()),
    ("INSERT INTO pages_servicefeature VALUES (1, 'JWT authentication', 1)", ()),
    ("INSERT INTO pages_servicefeature VALUES (2, 'API documentation', 1)", ()),
    ("INSERT INTO blog_category VALUES (1, 'Backend Development', 'backend-development', '')", ()),
    ("INSERT INTO blog_category VALUES (2, 'Python', 'python', '')", ()),
    ("INSERT INTO blog_tag VALUES (1, 'python', 'python')", ()),
    ("INSERT INTO blog_tag VALUES (2, 'telegram', 'telegram')", ()),
    ("INSERT INTO blog_article VALUES (1, 'Production Telegram bots', 'telegram-bots', 'Lessons.', ?, 1, "
     "'2026-06-22 10:44:30.722083', '2026-06-20 05:00:00', '2026-06-22 10:44:30', 1, 1, NULL)",
     ("# Production Telegram bots\n\nA *production* bot needs more.\n\n## Structure\n\nSplit `handlers/`.",)),
    ("INSERT INTO blog_article VALUES (2, 'Clean Python', 'clean-python', '', ?, 0, NULL, "
     "'2026-06-20 05:06:11', '2026-06-20 05:06:11', 1, 2, '')", ("<p>Draft <em>body</em></p>",)),
    ("INSERT INTO blog_article_tags VALUES (1, 1, 1)", ()),
    ("INSERT INTO blog_article_tags VALUES (2, 1, 2)", ()),
    ("INSERT INTO blog_article_tags VALUES (3, 2, 1)", ()),
    ("INSERT INTO core_contactmessage VALUES (1, 'Dana', 'dana@example.com', 'Bot', 'Need a bot.', "
     "'2026-05-01 09:30:00', 1, 0)", ()),
    ("INSERT INTO portfolio_project VALUES (1, 'Volunteers Telegram Bot', 'volunteers_bot', 'Manages volunteers.', "
     "'Full story.', 'https://github.com/A1isherDev/volunteers_bot', '', '2025-01-01 00:00:00', '2025-01-02 00:00:00', 1, 1, '')", ()),
    ("INSERT INTO portfolio_project VALUES (2, 'Pul Olami', 'pul-olami', 'A finance game.', 'Story.', "
     "'https://github.com/A1isherDev/iqtisodchi-bolajon-android-app.git', NULL, '2025-02-01 00:00:00', '2025-02-01 00:00:00', 0, 0, '')", ()),
    ("INSERT INTO portfolio_project VALUES (3, 'Offline thing', 'offline', 'No repo.', '', NULL, NULL, "
     "'2025-03-01 00:00:00', '2025-03-01 00:00:00', 0, 1, '')", ()),
    ("INSERT INTO portfolio_technology VALUES (1, 'aiogram', 'x', 'aiogram')", ()),
    ("INSERT INTO portfolio_technology VALUES (2, 'Redis', 'x', 'redis')", ()),
    ("INSERT INTO portfolio_technology VALUES (3, 'Flutter', 'x', 'flutter')", ()),
    ("INSERT INTO portfolio_project_technologies VALUES (1, 1, 1)", ()),
    ("INSERT INTO portfolio_project_technologies VALUES (2, 1, 2)", ()),
    ("INSERT INTO portfolio_project_technologies VALUES (3, 2, 3)", ()),
]


@pytest.fixture
def legacy_db(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript(LEGACY_SCHEMA)
    for sql, params in ROWS:
        conn.execute(sql, params)
    conn.commit()
    conn.close()
    return path


def run(path):
    out = StringIO()
    call_command("import_legacy", db=str(path), stdout=out)
    return out.getvalue()


def counts():
    return {m.__name__: m.objects.count() for m in (SocialLink, Experience, Skill, Service, Tag, Post, Project, ContactMessage)}


def test_imports_profile_from_site_setting_and_about(legacy_db):
    run(legacy_db)
    p = Profile.load()
    assert p.name == "Alisher M"
    assert p.headline == "Backend Developer & Software Engineer"
    assert p.bio == "I'm Alisher, a backend developer.\n\nI build APIs & bots."
    assert p.location == "Fergana, Uzbekistan"
    assert p.email == "alisher@example.com"


def test_imports_links_experience_skills_services(legacy_db):
    run(legacy_db)
    assert [(s.platform, s.label, s.url) for s in SocialLink.objects.all()] == [
        ("github", "GitHub", "https://github.com/A1isherDev"), ("telegram", "Telegram", "https://t.me/alisher"),
    ]
    current = Experience.objects.get(company="Najot Ta'lim")
    assert current.end_date is None and current.start_date == dt.date(2024, 9, 1)
    assert Experience.objects.get(company="Acme").end_date == dt.date(2023, 6, 30)
    assert {(s.name, s.group) for s in Skill.objects.all()} == {("Python", "Backend"), ("PostgreSQL", "Databases"), ("Docker", "DevOps")}
    service = Service.objects.get()
    assert service.title == "REST API Development"
    assert service.description == "Secure REST APIs.\n\n- JWT authentication\n- API documentation"


def test_imports_posts_as_html_with_tags_and_category(legacy_db):
    run(legacy_db)
    post = Post.objects.get(slug="telegram-bots")
    assert post.body_format == Post.Format.HTML
    assert post.status == Post.Status.PUBLISHED
    assert post.published_at == dt.datetime(2026, 6, 22, 10, 44, 30, 722083, tzinfo=dt.timezone.utc)
    assert "<em>production</em>" in post.body and "<h2>Structure</h2>" in post.body
    assert "<h1>" not in post.body and "Production Telegram bots</" not in post.body  # leading title heading dropped
    assert sorted(t.slug for t in post.tags.all()) == ["backend-development", "python", "telegram"]
    draft = Post.objects.get(slug="clean-python")
    assert draft.status == Post.Status.DRAFT and draft.published_at is None
    assert draft.body == "<p>Draft <em>body</em></p>"
    assert [t.slug for t in draft.tags.all()] == ["python"]  # tag and category "python" are one Tag
    assert draft.created_at == dt.datetime(2026, 6, 20, 5, 6, 11, tzinfo=dt.timezone.utc)


def test_imports_contact_messages(legacy_db):
    run(legacy_db)
    msg = ContactMessage.objects.get()
    assert (msg.name, msg.email, msg.is_read) == ("Dana", "dana@example.com", True)
    assert msg.message == "Subject: Bot\n\nNeed a bot."
    assert msg.created_at == dt.datetime(2026, 5, 1, 9, 30, tzinfo=dt.timezone.utc)


def test_seeds_projects_only_with_github_url(legacy_db):
    Repo.objects.create(github_id=7, name="volunteers_bot", full_name="A1isherDev/volunteers_bot",
                        url="https://github.com/A1isherDev/volunteers_bot")
    run(legacy_db)
    assert Project.objects.count() == 2
    bot = Project.objects.get(repo_full_name="A1isherDev/volunteers_bot")
    assert (bot.slug, bot.title, bot.summary, bot.case_study) == ("volunteers_bot", "Volunteers Telegram Bot", "Manages volunteers.", "Full story.")
    assert bot.kind == "Bot" and bot.stack == ["aiogram", "Redis"] and bot.featured and not bot.hidden
    assert bot.repo.full_name == "A1isherDev/volunteers_bot"
    game = Project.objects.get(repo_full_name="A1isherDev/iqtisodchi-bolajon-android-app")
    assert game.kind == "Android" and game.hidden and game.repo is None


def test_rerunning_creates_no_duplicates_and_keeps_edits(legacy_db):
    first = run(legacy_db)
    before = counts()
    p = Profile.load()
    p.headline = "Edited in the studio"
    p.save()
    second = run(legacy_db)
    assert counts() == before
    assert Profile.load().headline == "Edited in the studio"
    assert "posts: 2 new" in first and "posts: 0 new, 2 already there" in second


def test_missing_database_is_an_error(tmp_path):
    with pytest.raises(CommandError):
        call_command("import_legacy", db=str(tmp_path / "nope.sqlite3"))


def test_missing_tables_are_skipped(tmp_path):
    path = tmp_path / "empty.sqlite3"
    sqlite3.connect(path).close()
    out = run(path)
    assert "skipped" in out
    assert Post.objects.count() == 0
