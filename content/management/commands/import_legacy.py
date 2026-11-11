"""Import content from the old site (core_*, pages_*, blog_*, portfolio_* tables) into the Atlas models.

    manage.py import_legacy [--db PATH]

The old tables are read with the sqlite3 module, read-only. Re-running is safe: rows are matched on a
natural key and only missing rows are created; Profile fields are filled only while they are blank,
so edits made in the studio are kept.
"""
import datetime as dt
import re
import sqlite3
from html import unescape
from pathlib import Path

import markdown as md_lib
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.html import strip_tags
from django.utils.text import slugify

from content.models import Experience, Post, Profile, Project, Service, Skill, SocialLink, Tag
from content.rendering import MARKDOWN_EXTENSIONS, sanitize_html
from integrations.models import Repo
from web.models import ContactMessage

LEGACY_TABLES = (
    "core_sitesetting", "core_sociallink", "core_contactmessage", "pages_aboutsection", "pages_experience",
    "pages_skill", "pages_service", "pages_servicefeature", "blog_article", "blog_article_tags", "blog_tag",
    "blog_category", "portfolio_project", "portfolio_technology", "portfolio_project_technologies",
)
PLATFORM_LABELS = {
    "github": "GitHub", "linkedin": "LinkedIn", "telegram": "Telegram", "instagram": "Instagram",
    "twitter": "X", "x": "X", "facebook": "Facebook", "discord": "Discord", "youtube": "YouTube",
}
SKILL_GROUPS = {"backend": "Backend", "database": "Databases", "frontend": "Frontend", "devops": "DevOps", "other": "Other"}
GITHUB_URL = re.compile(r"^https?://(?:www\.)?github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9._-]+?)(?:\.git)?/?(?:[?#].*)?$")


def _dt(value):
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def _date(value):
    return dt.date.fromisoformat(str(value)[:10]) if value else None


def html_to_paragraphs(html):
    """Plain-text paragraphs (blank-line separated) from the old About HTML."""
    parts = re.split(r"</p\s*>|<br\s*/?>|</li\s*>|</h[1-6]\s*>|</div\s*>", html or "", flags=re.I)
    paras = [re.sub(r"\s+", " ", unescape(strip_tags(p))).strip() for p in parts]
    return "\n\n".join(p for p in paras if p)


def article_html(title, content):
    """Old articles were Markdown (rendered on view); store them as sanitized HTML."""
    lines = (content or "").lstrip().splitlines()
    if lines and lines[0].startswith("# ") and lines[0][2:].strip().lower() == title.strip().lower():
        lines = lines[1:]
    html = md_lib.markdown("\n".join(lines).strip(), extensions=MARKDOWN_EXTENSIONS, output_format="html")
    html = re.sub(r"<(/?)h1>", r"<\1h2>", html)
    return str(sanitize_html(html))


def guess_kind(title, slug, techs):
    text = f"{title} {slug}".lower()
    names = {t.lower() for t in techs}
    if "bot" in text.split() or "_bot" in text or "aiogram" in names:
        return "Bot"
    if names & {"flutter", "kotlin", "dart"} or "android" in text:
        return "Android"
    if any(word in text for word in ("platform", "lms", "academy", "exam")):
        return "Platform"
    return ""


class Command(BaseCommand):
    help = "Import content from the old site's tables into the Atlas models (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--db", help="Path to the old SQLite database. Default: the configured database.")

    def handle(self, *args, **options):
        path = Path(options["db"] or settings.DATABASES["default"]["NAME"])
        if not path.is_file():
            raise CommandError(f"No database at {path}. Pass --db with the path to the old db.sqlite3.")
        rows = self.read(path)
        self.stats = []
        with transaction.atomic():
            self.import_profile(rows)
            self.import_links(rows)
            self.import_experience(rows)
            self.import_skills(rows)
            self.import_services(rows)
            self.import_posts(rows)
            self.import_messages(rows)
            self.import_projects(rows)
        for line in self.stats:
            self.stdout.write(line)

    # --- reading ------------------------------------------------------------------------

    def read(self, path):
        """Every legacy table as a list of dicts (None when the table is missing)."""
        conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            return {t: [dict(r) for r in conn.execute(f'SELECT * FROM "{t}" ORDER BY id')] if t in present else None
                    for t in LEGACY_TABLES}
        except sqlite3.DatabaseError as exc:
            raise CommandError(f"Could not read {path}: {exc}") from exc
        finally:
            conn.close()

    def report(self, label, created, existing):
        self.stats.append(f"{label}: {created} new, {existing} already there")

    def skipped(self, label, table):
        self.stats.append(f"{label}: skipped (no {table} table)")

    # --- importers ----------------------------------------------------------------------

    def import_profile(self, rows):
        site = (rows["core_sitesetting"] or [None])[0]
        about = (rows["pages_aboutsection"] or [None])[0]
        if not site and not about:
            return self.skipped("profile", "core_sitesetting")
        site, about = site or {}, about or {}
        name = site.get("site_name") or re.sub(r"^\s*I['’]m\s+", "", site.get("hero_title") or "")
        values = {
            "name": name.strip(),
            "headline": (site.get("hero_subtitle") or "").strip(),
            "bio": html_to_paragraphs(about.get("content")) or (site.get("hero_description") or "").strip(),
            "location": (site.get("location") or about.get("location") or "").strip(),
            "email": (site.get("contact_email") or "").strip(),
        }
        profile = Profile.load()
        default_name = Profile._meta.get_field("name").default
        filled = []
        for field, value in values.items():
            current = getattr(profile, field)
            if value and (not current or (field == "name" and current == default_name and value != current)):
                setattr(profile, field, value)
                filled.append(field)
        if filled:
            profile.save()
        self.stats.append(f"profile: filled {', '.join(filled) if filled else 'nothing (already set)'}")

    def import_links(self, rows):
        if rows["core_sociallink"] is None:
            return self.skipped("social links", "core_sociallink")
        created = existing = 0
        for r in rows["core_sociallink"]:
            if not r["is_active"]:
                continue
            platform = (r["platform_name"] or "").strip().lower()
            _, made = SocialLink.objects.get_or_create(url=r["url"], defaults={
                "platform": platform, "label": PLATFORM_LABELS.get(platform, platform.title()), "order": r["order"]})
            created, existing = created + made, existing + (not made)
        self.report("social links", created, existing)

    def import_experience(self, rows):
        if rows["pages_experience"] is None:
            return self.skipped("experience", "pages_experience")
        created = existing = 0
        for r in rows["pages_experience"]:
            _, made = Experience.objects.get_or_create(
                company=r["company"], role=r["role"], start_date=_date(r["start_date"]),
                defaults={"description": r["description"] or "", "order": r["order"],
                          "end_date": None if r["is_current"] else _date(r["end_date"])})
            created, existing = created + made, existing + (not made)
        self.report("experience", created, existing)

    def import_skills(self, rows):
        if rows["pages_skill"] is None:
            return self.skipped("skills", "pages_skill")
        created = existing = 0
        for r in rows["pages_skill"]:  # the old percentage `level` is dropped on purpose
            group = (r["group"] or "").strip()
            if Skill.objects.filter(name__iexact=r["name"]).exists():
                existing += 1
                continue
            Skill.objects.create(name=r["name"], group=SKILL_GROUPS.get(group.lower(), group.title()), order=r["order"])
            created += 1
        self.report("skills", created, existing)

    def import_services(self, rows):
        if rows["pages_service"] is None:
            return self.skipped("services", "pages_service")
        features = {}
        for f in rows["pages_servicefeature"] or []:
            features.setdefault(f["service_id"], []).append(f["name"])
        created = existing = 0
        for r in rows["pages_service"]:
            description = (r["description"] or "").strip()
            if features.get(r["id"]):
                description += "\n\n" + "\n".join(f"- {name}" for name in features[r["id"]])
            _, made = Service.objects.get_or_create(title=r["title"], defaults={"description": description.strip(), "order": r["order"]})
            created, existing = created + made, existing + (not made)
        self.report("services", created, existing)

    def _tag(self, name, slug):
        slug = slug or slugify(name)
        tag = Tag.objects.filter(slug=slug).first() or Tag.objects.filter(name__iexact=name).first()
        return tag or Tag.objects.create(name=name, slug=slug)

    def import_posts(self, rows):
        if rows["blog_article"] is None:
            return self.skipped("posts", "blog_article")
        tags = {t["id"]: t for t in rows["blog_tag"] or []}
        categories = {c["id"]: c for c in rows["blog_category"] or []}
        links = {}
        for link in rows["blog_article_tags"] or []:
            links.setdefault(link["article_id"], []).append(link["tag_id"])
        tags_before = Tag.objects.count()
        created = existing = 0
        for r in rows["blog_article"]:
            if Post.objects.filter(slug=r["slug"]).exists():
                existing += 1
                continue
            published = bool(r["published"])
            post = Post.objects.create(
                title=r["title"], slug=r["slug"], excerpt=(r["excerpt"] or "").strip(),
                body=article_html(r["title"], r["content"]), body_format=Post.Format.HTML,
                status=Post.Status.PUBLISHED if published else Post.Status.DRAFT,
                published_at=(_dt(r["published_at"]) or _dt(r["created_at"])) if published else None,
                cover=r.get("cover") or "",
            )
            post_tags = [self._tag(tags[t]["name"], tags[t]["slug"]) for t in links.get(r["id"], []) if t in tags]
            category = categories.get(r["category_id"])
            if category:
                post_tags.append(self._tag(category["name"], category["slug"]))
            post.tags.set({t.pk: t for t in post_tags}.values())
            Post.objects.filter(pk=post.pk).update(created_at=_dt(r["created_at"]))
            created += 1
        self.report("posts", created, existing)
        self.stats.append(f"tags: {Tag.objects.count() - tags_before} new")

    def import_messages(self, rows):
        if rows["core_contactmessage"] is None:
            return self.skipped("contact messages", "core_contactmessage")
        created = existing = 0
        for r in rows["core_contactmessage"]:
            sent = _dt(r["created_at"])
            if ContactMessage.objects.filter(email=r["email"], name=r["name"][:120], created_at=sent).exists():
                existing += 1
                continue
            subject = (r["subject"] or "").strip()
            body = f"Subject: {subject}\n\n{r['message']}" if subject else r["message"]
            msg = ContactMessage.objects.create(name=r["name"][:120], email=r["email"], message=body, is_read=bool(r["is_read"]))
            ContactMessage.objects.filter(pk=msg.pk).update(created_at=sent)
            created += 1
        self.report("contact messages", created, existing)

    def import_projects(self, rows):
        if rows["portfolio_project"] is None:
            return self.skipped("projects", "portfolio_project")
        tech_names = {t["id"]: t["name"] for t in rows["portfolio_technology"] or []}
        stacks = {}
        for link in rows["portfolio_project_technologies"] or []:
            if link["technology_id"] in tech_names:
                stacks.setdefault(link["project_id"], []).append(tech_names[link["technology_id"]])
        created = existing = without_repo = 0
        for position, r in enumerate(rows["portfolio_project"], start=1):
            match = GITHUB_URL.match((r["github_url"] or "").strip())
            if not match:
                without_repo += 1
                continue
            full_name = f"{match.group(1)}/{match.group(2)}"
            if Project.objects.filter(repo_full_name__iexact=full_name).exists():
                existing += 1
                continue
            slug = r["slug"] or slugify(r["title"])
            if Project.objects.filter(slug=slug).exists():
                slug = f"{slug}-{position}"
            stack = stacks.get(r["id"], [])
            project = Project.objects.create(
                repo_full_name=full_name, slug=slug, title=r["title"], summary=(r["short_description"] or "").strip(),
                case_study=(r["description"] or "").strip(), kind=guess_kind(r["title"], r["slug"] or "", stack),
                stack=stack, featured=bool(r["is_featured"]), hidden=not r["is_active"], order=position,
                repo=Repo.objects.filter(full_name__iexact=full_name, project__isnull=True).first(),
            )
            Project.objects.filter(pk=project.pk).update(created_at=_dt(r["created_at"]))
            created += 1
        self.report("projects", created, existing)
        if without_repo:
            self.stats.append(f"projects without a GitHub URL (not imported): {without_repo}")
