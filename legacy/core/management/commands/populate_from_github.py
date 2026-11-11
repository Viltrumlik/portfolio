"""
Populate the whole portfolio with real content for A1isherDev (Alisher
Muhammadaliyev): identity, socials, skills, projects (with generated preview
cards + full technology lists), experience, services, blog and SEO.

Merges curated English content (core/data/github_content.py) with live GitHub
metadata (repo list, per-repo languages, avatar). Idempotent — safe to re-run.

Usage:
    python manage.py populate_from_github [--user A1isherDev] [--skip-cards]
"""
import datetime
import json
import os
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from core.models import SiteSetting, SocialLink, SEO
from pages.models import Skill, Experience, AboutSection, Service, ServiceFeature
from portfolio.models import Technology, Project
from blog.models import Category, Tag, Article

from core.data import github_content as gc
from core.utils.preview_cards import generate_card


def _api(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "guts-portfolio-importer", "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "guts-portfolio-importer"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


class Command(BaseCommand):
    help = "Populate the site with real content sourced from GitHub (A1isherDev)."

    def add_arguments(self, parser):
        parser.add_argument("--user", default=gc.GITHUB_USER)
        parser.add_argument("--skip-cards", action="store_true",
                            help="Do not (re)generate project preview cards.")

    # ── helpers ────────────────────────────────────────────────────────────
    def _write_media(self, rel_path, data):
        """Write bytes to MEDIA_ROOT/<rel_path>, overwriting (stable filename)."""
        full = os.path.join(settings.MEDIA_ROOT, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
        return rel_path

    def _tech(self, name):
        """get_or_create a Technology, ensuring an icon class from the curated map."""
        tech, _ = Technology.objects.get_or_create(
            name=name, defaults={"icon_class": gc.TECH_ICONS.get(name, "")}
        )
        icon = gc.TECH_ICONS.get(name)
        if icon and tech.icon_class != icon:
            tech.icon_class = icon
            tech.save(update_fields=["icon_class"])
        return tech

    def _clean_langs(self, langs):
        out = []
        for lang in langs:
            lang = gc.LANG_RENAME.get(lang, lang)
            if lang in gc.LANG_DROP or lang in out:
                continue
            out.append(lang)
        return out

    # ── main ───────────────────────────────────────────────────────────────
    def handle(self, *args, **opts):
        user = opts["user"]
        make_cards = not opts["skip_cards"]
        I = gc.IDENTITY

        self.stdout.write(self.style.MIGRATE_HEADING(f"Populating from github.com/{user} …"))

        # 1. SiteSetting + avatar -------------------------------------------------
        ss = SiteSetting.get_singleton()
        ss.site_name = I["site_name"]
        ss.hero_title = I["hero_title"]
        ss.hero_subtitle = I["hero_subtitle"]
        ss.hero_greeting = I["hero_greeting"]
        ss.hero_description = I["hero_description"]
        ss.contact_email = I["contact_email"]
        ss.location = I["location"]
        try:
            avatar_url = _api(f"https://api.github.com/users/{user}").get("avatar_url") or gc.AVATAR_URL
        except Exception:
            avatar_url = gc.AVATAR_URL
        try:
            ss.logo.name = self._write_media("core/avatar.png", _download(avatar_url))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  avatar download failed: {e}"))
        ss.save()
        self.stdout.write("  ✓ SiteSetting + avatar")

        # 2. Social links (rebuild from curated set) ------------------------------
        SocialLink.objects.all().delete()
        for platform, url, icon, order in gc.SOCIALS:
            SocialLink.objects.create(platform_name=platform, url=url,
                                      icon_class=icon, order=order, is_active=True)
        self.stdout.write(f"  ✓ {len(gc.SOCIALS)} social links")

        # 3. AboutSection ---------------------------------------------------------
        ab = AboutSection.get_singleton()
        ab.title = I["about_title"]
        ab.content = I["about_content"]
        ab.education = I["education"]
        ab.location = I["location"]
        ab.languages = I["languages_spoken"]
        ab.years_experience = I["years_experience"]
        ab.projects_completed = I["projects_completed"]
        ab.happy_clients = I["happy_clients"]
        ab.save()
        self.stdout.write("  ✓ AboutSection")

        # 4. Skills (rebuild) -----------------------------------------------------
        Skill.objects.all().delete()
        for order, (name, group, level, icon) in enumerate(gc.SKILLS, start=1):
            Skill.objects.create(name=name, group=group, level=level,
                                 icon_class=icon, order=order)
        self.stdout.write(f"  ✓ {len(gc.SKILLS)} skills")

        # 5. Projects (curated text + live languages w/ fallback + cards) ---------
        # Build a live repo map (html_url, homepage) when the API is reachable.
        repo_map = {}
        try:
            for repo in _api(f"https://api.github.com/users/{user}/repos?per_page=100"):
                repo_map[repo["name"]] = repo
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  repo list API unavailable ({e}); using curated data"))

        seen_slugs = set()
        n_created = n_updated = 0
        for name, cur in gc.PROJECTS.items():
            if name in gc.SKIP_REPOS:
                continue
            slug = slugify(name)
            seen_slugs.add(slug)
            repo = repo_map.get(name, {})

            try:
                langs = list(_api(f"https://api.github.com/repos/{user}/{name}/languages").keys())
            except Exception:
                langs = gc.LANGUAGES.get(name, [])
            # frameworks first (more meaningful), then languages; capped.
            tech_names, ordered = [], list(cur.get("extra_tech", [])) + self._clean_langs(langs)
            for t in ordered:
                if t and t not in tech_names:
                    tech_names.append(t)
            tech_names = tech_names[:8]

            obj, created = Project.objects.get_or_create(slug=slug, defaults={"title": cur["title"]})
            obj.title = cur["title"]
            obj.short_description = cur["short_description"][:500]
            obj.description = cur["long_description"]
            obj.github_url = repo.get("html_url") or f"https://github.com/{user}/{name}"
            obj.live_url = (repo.get("homepage") or "").strip() or None
            obj.is_featured = cur.get("is_featured", False)
            obj.is_active = True

            if make_cards:
                try:
                    png = generate_card(cur["title"], tech_names, f"{user}/{name}")
                    obj.image.name = self._write_media(f"projects/{slug}.png", png)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"    card failed for {name}: {e}"))
            obj.save()
            obj.technologies.set([self._tech(t) for t in tech_names])
            n_created += created
            n_updated += (not created)
        self.stdout.write(f"  ✓ Projects: {n_created} created, {n_updated} updated")

        # Deactivate any project no longer backed by curated content (e.g. old seeds)
        stale = Project.objects.exclude(slug__in=seen_slugs)
        if stale.exists():
            self.stdout.write(self.style.WARNING(
                f"    removing {stale.count()} stale project(s): "
                + ", ".join(stale.values_list('title', flat=True))))
            stale.delete()

        # 6. Experience (rebuild) -------------------------------------------------
        Experience.objects.all().delete()
        for e in gc.EXPERIENCE:
            Experience.objects.create(
                company=e["company"], role=e["role"], description=e["description"],
                start_date=datetime.date.fromisoformat(e["start"]),
                end_date=datetime.date.fromisoformat(e["end"]) if e["end"] else None,
                is_current=e["is_current"], order=e["order"],
            )
        self.stdout.write(f"  ✓ {len(gc.EXPERIENCE)} experience entries")

        # 7. Services (rebuild) ---------------------------------------------------
        Service.objects.all().delete()
        for s in gc.SERVICES:
            svc = Service.objects.create(title=s["title"], description=s["description"],
                                         icon_class=s["icon_class"], order=s["order"])
            for feat in s["features"]:
                ServiceFeature.objects.create(service=svc, name=feat)
        self.stdout.write(f"  ✓ {len(gc.SERVICES)} services")

        # 8. Blog (upsert) --------------------------------------------------------
        for a in gc.ARTICLES:
            category, _ = Category.objects.get_or_create(
                name=a["category"], defaults={"slug": slugify(a["category"])})
            art, _ = Article.objects.update_or_create(
                slug=a["slug"],
                defaults={
                    "title": a["title"],
                    "excerpt": a["excerpt"][:500],
                    "content": a["content"],
                    "category": category,
                    "published": True,
                },
            )
            if not art.published_at:
                art.published_at = timezone.now()
                art.save(update_fields=["published_at"])
            art.tags.set([Tag.objects.get_or_create(
                name=t, defaults={"slug": slugify(t)})[0] for t in a["tags"]])
        self.stdout.write(f"  ✓ {len(gc.ARTICLES)} articles")

        # 9. SEO ------------------------------------------------------------------
        for s in gc.SEO_DATA:
            SEO.objects.update_or_create(
                page_key=s["page_key"],
                defaults={"meta_title": s["meta_title"],
                          "meta_description": s["meta_description"],
                          "meta_keywords": s["meta_keywords"]},
            )
        self.stdout.write(f"  ✓ {len(gc.SEO_DATA)} SEO entries")

        self.stdout.write(self.style.SUCCESS("Done. Site populated from GitHub."))
