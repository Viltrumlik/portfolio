"""Content: the profile, simple collections (experience, skills, services, links), posts and project curation."""
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from automations.events import emit
from content.models import Experience, Post, Profile, Project, Service, Skill, SocialLink

from ..forms import ExperienceForm, PostForm, ProfileForm, ProjectForm, ServiceForm, SkillForm, SocialLinkForm


def _dates(job):
    end = f"{job.end_date:%b %Y}" if job.end_date else "Present"
    return f"{job.start_date:%b %Y} — {end}"


COLLECTIONS = {
    "experience": {
        "model": Experience, "form": ExperienceForm, "title": "Experience", "noun": "experience",
        "row": lambda o: {"key": _dates(o), "title": o.role, "meta": " · ".join(filter(None, [o.company, o.location]))},
    },
    "skills": {
        "model": Skill, "form": SkillForm, "title": "Skills", "noun": "skill",
        "row": lambda o: {"key": o.group or "Ungrouped", "title": o.name, "meta": f"Order {o.order}"},
    },
    "services": {
        "model": Service, "form": ServiceForm, "title": "Services", "noun": "service",
        "row": lambda o: {"key": f"#{o.order}", "title": o.title, "meta": o.description[:140]},
    },
    "links": {
        "model": SocialLink, "form": SocialLinkForm, "title": "Social links", "noun": "link",
        "row": lambda o: {"key": o.platform, "title": o.label or o.platform, "meta": o.url},
    },
}


def _collection(kind):
    try:
        return COLLECTIONS[kind]
    except KeyError:
        raise Http404("Unknown collection") from None


# --- index + profile ------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
def index(request):
    profile = Profile.load()
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved.")
        return redirect("studio:content")
    sections = [
        {"label": spec["title"], "href": reverse("studio:items", args=[kind]), "count": spec["model"].objects.count()}
        for kind, spec in COLLECTIONS.items()
    ] + [
        {"label": "Posts", "href": reverse("studio:posts"), "count": Post.objects.count()},
        {"label": "Projects", "href": reverse("studio:projects"), "count": Project.objects.count()},
    ]
    return render(request, "studio/content.html", {"form": form, "sections": sections})


# --- simple collections ---------------------------------------------------------------


@require_GET
def item_list(request, kind):
    spec = _collection(kind)
    rows = [{**spec["row"](obj), "href": reverse("studio:item", args=[kind, obj.pk])} for obj in spec["model"].objects.all()]
    return render(request, "studio/list.html", {
        "window_title": f"content/{kind}",
        "heading": spec["title"],
        "rows": rows,
        "empty": f"No {spec['title'].lower()} yet.",
        "new_url": reverse("studio:item_new", args=[kind]),
        "new_label": f"Add {spec['noun']}",
    })


@require_http_methods(["GET", "POST"])
def item_edit(request, kind, pk=None):
    spec = _collection(kind)
    obj = get_object_or_404(spec["model"], pk=pk) if pk else None
    form = spec["form"](request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{spec['noun'].capitalize()} saved.")
        return redirect("studio:items", kind)
    return render(request, "studio/form_page.html", {
        "window_title": f"content/{kind}/{'edit' if obj else 'new'}",
        "heading": f"Edit {spec['noun']}" if obj else f"Add {spec['noun']}",
        "form": form,
        "submit_label": f"Save {spec['noun']}",
        "back_url": reverse("studio:items", args=[kind]),
        "back_label": f"Back to {spec['title'].lower()}",
        "delete_url": reverse("studio:item_delete", args=[kind, obj.pk]) if obj else None,
        "delete_label": f"Delete {spec['noun']}",
    })


@require_POST
def item_delete(request, kind, pk):
    spec = _collection(kind)
    obj = get_object_or_404(spec["model"], pk=pk)
    obj.delete()
    messages.success(request, f"{spec['noun'].capitalize()} deleted.")
    return redirect("studio:items", kind)


# --- posts ----------------------------------------------------------------------------


@require_GET
def post_list(request):
    rows = [
        {
            "key": f"{post.published_at:%b %d, %Y}" if post.published_at else "Not published",
            "title": post.title,
            "meta": " · ".join(filter(None, [post.slug, ", ".join(t.name for t in post.tags.all())])),
            "badge": {"label": post.get_status_display(), "tone": "live" if post.status == Post.Status.PUBLISHED else "neutral"},
            "href": reverse("studio:post", args=[post.pk]),
        }
        for post in Post.objects.prefetch_related("tags").order_by("-created_at", "-pk")
    ]
    return render(request, "studio/list.html", {
        "window_title": "writing/",
        "heading": "Posts",
        "rows": rows,
        "empty": "No posts yet.",
        "new_url": reverse("studio:post_new"),
        "new_label": "New post",
    })


def _announce(post):
    """Emit post.published once per post, ever (external_id makes a repeat a no-op)."""
    url = settings.SITE_URL.rstrip("/") + post.get_absolute_url()
    emit("post.published", {"title": post.title, "url": url}, source="site", public=True, external_id=f"post.published:{post.pk}")


@require_http_methods(["GET", "POST"])
def post_edit(request, pk=None):
    post = get_object_or_404(Post, pk=pk) if pk else None
    was_published = bool(post and post.status == Post.Status.PUBLISHED)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            saved = form.save(commit=False)
            publishing = saved.status == Post.Status.PUBLISHED and not was_published
            if publishing and not saved.published_at:
                saved.published_at = timezone.now()
            saved.save()
            form.save_tags(saved)
            if publishing:
                _announce(saved)
        messages.success(request, "Post published." if publishing else "Post saved.")
        return redirect("studio:post", saved.pk)
    return render(request, "studio/form_page.html", {
        "window_title": f"writing/{post.slug}.md" if post else "writing/new.md",
        "heading": "Edit post" if post else "New post",
        "form": form,
        "wide": True,
        "submit_label": "Save post",
        "back_url": reverse("studio:posts"),
        "back_label": "Back to posts",
        "view_url": post.get_absolute_url() if post and post.status == Post.Status.PUBLISHED else None,
    })


# --- projects -------------------------------------------------------------------------


@require_GET
def project_list(request):
    rows = []
    for project in Project.objects.select_related("repo"):
        flags = [label for label, on in (("Featured", project.featured), ("Hidden", project.hidden)) if on]
        rows.append({
            "key": f"#{project.order}",
            "title": project.display_title,
            "meta": " · ".join(filter(None, [project.repo_full_name, project.kind, ", ".join(map(str, project.stack))])),
            "badge": {"label": " · ".join(flags), "tone": "live" if project.featured else "neutral"} if flags else None,
            "href": reverse("studio:project", args=[project.pk]),
        })
    return render(request, "studio/list.html", {
        "window_title": "projects/",
        "heading": "Projects",
        "intro": "Projects come from GitHub syncs. Curate how each one shows on the site.",
        "rows": rows,
        "empty": "No projects yet. Connect GitHub and sync to import them.",
    })


@require_http_methods(["GET", "POST"])
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, request.FILES or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"“{project.display_title}” saved.")
        return redirect("studio:projects")
    return render(request, "studio/form_page.html", {
        "window_title": f"projects/{project.slug}",
        "heading": project.display_title,
        "intro": project.repo_full_name,
        "form": form,
        "wide": True,
        "submit_label": "Save project",
        "back_url": reverse("studio:projects"),
        "back_label": "Back to projects",
        "view_url": project.get_absolute_url() if not project.hidden else None,
    })
