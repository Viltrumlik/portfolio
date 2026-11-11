"""Site-wide navigation data: menu bar links and the ⌘K command palette."""
from django.urls import reverse
from django.utils import timezone

from content.models import Post, Project

NAV_LINKS = [("Work", "/work/"), ("Writing", "/writing/"), ("About", "/about/"), ("Contact", "/contact/")]


def visible_projects():
    return Project.objects.filter(hidden=False).select_related("repo")


def published_posts():
    return Post.objects.filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now()).order_by("-published_at")


def command_palette(profile, is_staff=False):
    pages = [{"label": "Home", "hint": "/", "icon": "arrow-right", "href": "/", "keywords": "start desk"}] + [
        {"label": label, "hint": href, "icon": "arrow-right", "href": href, "keywords": label.lower()}
        for label, href in NAV_LINKS
    ]
    projects = [
        {
            "label": p.display_title,
            "hint": p.kind or (p.repo.language if p.repo else ""),
            "icon": "code",
            "href": reverse("web:project", args=[p.slug]),
            "keywords": " ".join([p.repo_full_name, *[str(s) for s in p.stack]]),
        }
        for p in visible_projects()
    ]
    writing = [
        {
            "label": post.title,
            "hint": f"{post.published_at:%b} {post.published_at.year}",
            "icon": "commit",
            "href": reverse("web:post", args=[post.slug]),
            "keywords": " ".join(t.name for t in post.tags.all()),
        }
        for post in published_posts().prefetch_related("tags")[:10]
    ]
    actions = [{"label": "Switch theme", "action": "theme", "icon": "power", "keywords": "dark light sage pulse"}]
    if profile.email:
        actions.append({"label": "Copy email address", "action": f"copy:{profile.email}", "icon": "link", "keywords": "mail contact"})
    if profile.cv:
        actions.append({"label": "Download CV", "href": profile.cv.url, "icon": "arrow-up-right", "keywords": "resume"})
    if is_staff:
        actions.append({"label": "Open studio", "href": "/studio/", "icon": "zap", "keywords": "admin owner"})
    groups = [{"label": "Pages", "items": pages}]
    if projects:
        groups.append({"label": "Projects", "items": projects})
    if writing:
        groups.append({"label": "Writing", "items": writing})
    groups.append({"label": "Actions", "items": actions})
    return {"groups": groups}
