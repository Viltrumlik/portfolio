import datetime as dt

from django.utils import timezone

from content.models import Post, Profile, Project, Tag
from integrations.models import Repo


def profile(**fields):
    p = Profile.load()
    defaults = {
        "name": "Alisher Muhammadaliyev", "handle": "alisher.os", "headline": "I build backends that keep working",
        "bio": "I build server-side systems, REST APIs and bots.\n\nSecond paragraph.",
        "location": "Fergana, Uzbekistan", "email": "me@example.com",
    }
    for k, v in {**defaults, **fields}.items():
        setattr(p, k, v)
    p.save()
    return p


def repo(name, language="Python", **fields):
    defaults = {"github_id": abs(hash(name)) % 10**9, "name": name, "full_name": f"a1/{name}",
                "url": f"https://github.com/a1/{name}", "language": language}
    return Repo.objects.create(**{**defaults, **fields})


def project(slug, **fields):
    defaults = {"repo_full_name": f"a1/{slug}", "slug": slug, "title": slug.replace("-", " ").title(), "summary": f"{slug} summary."}
    return Project.objects.create(**{**defaults, **fields})


def post(slug, status=Post.Status.PUBLISHED, days_ago=1, tags=(), **fields):
    defaults = {"title": slug.replace("-", " ").title(), "slug": slug, "excerpt": f"About {slug}.", "body": "Body **text**.",
                "status": status, "published_at": timezone.now() - dt.timedelta(days=days_ago)}
    obj = Post.objects.create(**{**defaults, **fields})
    for name in tags:
        tag, _ = Tag.objects.get_or_create(slug=name.lower(), defaults={"name": name})
        obj.tags.add(tag)
    return obj
