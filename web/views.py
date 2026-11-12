import hashlib
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from automations.events import emit
from content.models import Experience, Profile, Service, SocialLink, Skill, Tag
from content.rendering import excerpt, render_body, render_markdown
from integrations.models import Connection, ContributionDay, Repo

from integrations.services import contribution_total

from . import desk, live, og
from .forms import ContactForm
from .models import ContactMessage
from .site import published_posts, visible_projects

CONTACT_RATE_LIMIT = 5
CONTACT_RATE_WINDOW = 3600  # seconds

PAGE_OG = {
    "home": ("about.md", None),
    "work": ("projects/", "Things I built and still maintain"),
    "writing": ("writing/", "Notes from building things"),
    "about": ("about.md", "About me"),
    "contact": ("contact.md", "Write to me"),
}


def page_meta(request, title=None, description=None, og_kind="page", og_slug="home", type="website"):
    """Title, description, canonical URL and Open Graph values for base.html."""
    profile = Profile.load()
    base = settings.SITE_URL.rstrip("/")
    description = (description or profile.headline or "").strip()
    if len(description) > 200:
        description = description[:197].rsplit(" ", 1)[0] + "…"
    return {
        "title": f"{title} · {profile.name}" if title else profile.name,
        "og_title": title or profile.name,
        "description": description,
        "canonical": base + request.path,
        "image": base + reverse("web:og", args=[og_kind, og_slug]),
        "type": type,
        "site_name": profile.name,
    }


# --- home ---------------------------------------------------------------------------------


def _dock_items(has_github):
    items = []
    if has_github:
        items.append({"code": "GH", "label": "Work on GitHub", "href": reverse("web:work")})
    telegram = Connection.objects.filter(provider=Connection.Provider.TELEGRAM, status=Connection.Status.CONNECTED).exists()
    items.append({"code": "TG" if telegram else "@", "label": "Contact", "href": reverse("web:contact")})
    items.append({"code": "RS", "label": "RSS feed", "href": reverse("web:feed")})
    return items


def home(request):
    profile = Profile.load()
    projects = visible_projects()
    featured = list(projects.filter(featured=True)[:6]) or list(projects[:4])
    pinned = list(Repo.objects.filter(pinned=True)[:6])
    events = live.public_events(8)
    posts = list(published_posts().prefetch_related("tags")[:3])
    has_graph = ContributionDay.objects.exists()
    has_github = has_graph or Repo.objects.exists() or Connection.objects.filter(
        provider=Connection.Provider.GITHUB, status=Connection.Status.CONNECTED).exists()

    order = [name for name, shown in (("work", featured), ("activity", pinned or events), ("writing", posts), ("contact", True)) if shown]
    skills = list(Skill.objects.all())
    social_links = list(SocialLink.objects.all())
    project_total = projects.count()
    commits = contribution_total()
    sys_stats = [s for s in (
        {"value": commits, "label": "Commits this year"} if commits is not None else None,
        {"value": project_total, "label": "Projects"},
        {"value": published_posts().count(), "label": "Posts"},
        {"value": Repo.objects.count(), "label": "Repos"} if has_github else None,
    ) if s]
    layout = desk.desk_layout({
        "about": True, "terminal": True, "now": True, "graph": has_graph, "projects": bool(featured),
        "links": bool(social_links), "stack": bool(skills), "activity": bool(events), "stats": True,
    })
    return render(request, "web/home.html", {
        "seo": page_meta(request),
        "bio_excerpt": excerpt(profile.bio, words=20),
        "has_graph": has_graph,
        "desk": layout,
        "win": layout["windows"],
        "terminal": desk.terminal_transcript(profile, project_total, events),
        "stack_cfg": desk.stack_config(skills),
        "social_links": social_links,
        "sys_stats": sys_stats,
        "project_total": project_total,
        "dock_items": _dock_items(has_github),
        "featured": featured,
        "work_title": f"projects — {len(featured)} item{'' if len(featured) == 1 else 's'}",
        "pinned_repos": pinned,
        "events": events,
        "posts": posts,
        "idx": {name: f"{i:02d}" for i, name in enumerate(order, start=1)},
        "form": ContactForm(),
    })


# --- work ---------------------------------------------------------------------------------


def _languages(project):
    names = {s.lower() for s in project.stack if isinstance(s, str)}
    if project.repo and project.repo.language:
        names.add(project.repo.language.lower())
    return names


def work(request):
    projects = list(visible_projects())
    lang = request.GET.get("lang", "").strip()
    seen = {}
    for p in projects:
        if p.repo and p.repo.language:
            seen.setdefault(p.repo.language.lower(), p.repo.language)
    filters = [{"label": "All", "href": reverse("web:work"), "active": not lang}] + [
        {"label": name, "href": "?" + urlencode({"lang": name}), "active": lang.lower() == key}
        for key, name in sorted(seen.items())
    ]
    if lang:
        projects = [p for p in projects if lang.lower() in _languages(p)]
    return render(request, "web/work_list.html", {
        "seo": page_meta(request, "Work", "Projects I built and still maintain.", og_slug="work"),
        "projects": projects,
        "filters": filters,
        "lang": lang,
    })


def project(request, slug):
    obj = get_object_or_404(visible_projects(), slug=slug)
    repo = obj.repo
    return render(request, "web/work_detail.html", {
        "seo": page_meta(request, obj.display_title, obj.summary or (repo.description if repo else ""), "project", obj.slug, "article"),
        "project": obj,
        "repo": repo,
        "repo_url": repo.url if repo else f"https://github.com/{obj.repo_full_name}",
        "updated": live.relative(repo.pushed_at) if repo else "",
        "case_study_html": render_markdown(obj.case_study),
    })


# --- writing ------------------------------------------------------------------------------


def writing(request):
    posts = list(published_posts().prefetch_related("tags"))
    tags = Tag.objects.filter(posts__in=[p.pk for p in posts]).distinct()
    return render(request, "web/writing_list.html", {
        "seo": page_meta(request, "Writing", "Notes from building backends and bots.", og_slug="writing"),
        "posts": posts,
        "tags": tags,
        "heading": "Notes from building things",
    })


def writing_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = list(published_posts().filter(tags=tag).prefetch_related("tags"))
    if not posts:
        raise Http404("No published posts with this tag")
    return render(request, "web/writing_list.html", {
        "seo": page_meta(request, f"Posts tagged {tag.name}", f"Writing about {tag.name}.", og_slug="writing"),
        "posts": posts,
        "tag": tag,
        "heading": f"Posts tagged “{tag.name}”",
    })


def post(request, slug):
    obj = get_object_or_404(published_posts().prefetch_related("tags"), slug=slug)
    description = obj.excerpt or excerpt(obj.body, words=30, body_format=obj.body_format)
    return render(request, "web/writing_detail.html", {
        "seo": page_meta(request, obj.title, description, "post", obj.slug, "article"),
        "post": obj,
        "body_html": render_body(obj.body, obj.body_format),
    })


# --- about / contact ----------------------------------------------------------------------


def about(request):
    profile = Profile.load()
    groups = {}
    for skill in Skill.objects.all():
        groups.setdefault(skill.group or "Other", []).append(skill)
    return render(request, "web/about.html", {
        "seo": page_meta(request, "About", excerpt(profile.bio, words=30) or profile.headline, og_slug="about"),
        "bio_html": render_markdown(profile.bio),
        "experience": [(e, render_markdown(e.description)) for e in Experience.objects.all()],
        "skill_groups": sorted(groups.items()),
        "services": [(s, render_markdown(s.description)) for s in Service.objects.all()],
        "links": SocialLink.objects.all(),
    })


def client_ip(request):
    """The visitor's IP. nginx sets X-Real-IP (and appends to X-Forwarded-For); gunicorn on a unix socket has no REMOTE_ADDR."""
    real = request.META.get("HTTP_X_REAL_IP", "").strip()
    if real:
        return real
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def hash_ip(ip):
    return hashlib.sha256(f"{settings.SECRET_KEY}:{ip}".encode()).hexdigest()


def _count_submission(key):
    if not cache.add(key, 1, CONTACT_RATE_WINDOW):
        try:
            cache.incr(key)
        except ValueError:  # expired between add and incr
            cache.set(key, 1, CONTACT_RATE_WINDOW)


def contact(request):
    status = 200
    if request.method == "POST":
        form = ContactForm(request.POST)
        ip_hash = hash_ip(client_ip(request))
        rate_key = f"contact:rate:{ip_hash}"
        if (cache.get(rate_key) or 0) >= CONTACT_RATE_LIMIT:
            form.is_valid()
            form.add_error(None, "Too many messages from your network. Try again in an hour.")
            status = 429
        elif form.is_valid():
            data = form.cleaned_data
            if not data["website"]:  # the honeypot stayed empty: a person
                with transaction.atomic():
                    msg = ContactMessage.objects.create(name=data["name"], email=data["email"], message=data["message"], ip_hash=ip_hash)
                    emit("contact.submitted", {"id": msg.pk, "name": msg.name, "email": msg.email, "message": msg.message}, source="site")
                _count_submission(rate_key)
            messages.success(request, f"Thanks, {data['name']}. Your message reached me, and I'll reply to {data['email']}.")
            return redirect("web:contact")
    else:
        form = ContactForm()
    return render(request, "web/contact.html", {
        "seo": page_meta(request, "Contact", "Write to me about a project, a job or a bot that needs building.", og_slug="contact"),
        "form": form,
    }, status=status)


# --- live JSON ----------------------------------------------------------------------------


@require_GET
def live_now(request):
    avail = live.availability(Profile.load())
    response = JsonResponse({
        "listening": live.listening_payload(live.current_listening()),
        "availability": {"status": avail["status"], "label": avail["label"]},
    })
    response["Cache-Control"] = "public, max-age=30"
    return response


@require_GET
def live_activity(request):
    tz = Profile.load().timezone
    response = JsonResponse({"items": [live.event_item(e, tz) for e in live.public_events(10)]})
    response["Cache-Control"] = "public, max-age=60"
    return response


# --- SEO ----------------------------------------------------------------------------------


@require_GET
def robots(request):
    base = settings.SITE_URL.rstrip("/")
    body = "\n".join([
        "User-agent: *",
        "Disallow: /studio/",
        "Disallow: /admin/",
        "Disallow: /api/",
        f"Sitemap: {base}{reverse('web:sitemap')}",
        "",
    ])
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_GET
def og_image(request, kind, slug):
    profile = Profile.load()
    if kind == "page":
        if slug not in PAGE_OG:
            raise Http404("Unknown page")
        label, title = PAGE_OG[slug]
        title = title or profile.headline or profile.name
        subtitle = profile.name if slug == "home" else (profile.headline or "")
    elif kind == "project":
        obj = get_object_or_404(visible_projects(), slug=slug)
        title, subtitle, label = obj.display_title, obj.summary, f"projects/{slug}.md"
    elif kind == "post":
        obj = get_object_or_404(published_posts(), slug=slug)
        title, subtitle, label = obj.title, obj.excerpt, f"writing/{slug}.md"
    else:
        raise Http404("Unknown image kind")
    path = og.image_path(kind, slug, title, subtitle or "", label, profile.handle or "")
    response = FileResponse(open(path, "rb"), content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    return response
