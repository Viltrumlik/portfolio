"""The Telegram channel queue: posts the job runner publishes at their time. Times are shown in the owner's zone."""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from automations.models import ScheduledPost
from content.models import Profile
from integrations.models import Connection

from ..forms import ScheduledPostForm

BADGES = {
    ScheduledPost.Status.SCHEDULED: "neutral",
    ScheduledPost.Status.QUEUED: "accent",
    ScheduledPost.Status.POSTED: "live",
    ScheduledPost.Status.FAILED: "danger",
    ScheduledPost.Status.CANCELLED: "neutral",
}


def _zone():
    name = Profile.load().timezone or "UTC"
    try:
        return name, ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return "UTC", ZoneInfo("UTC")


def _channel():
    conn = Connection.objects.filter(provider="telegram").first()
    return ((conn.config or {}).get("channel_id") if conn else "") or ""


@require_GET
def post_list(request):
    tz_name, tz = _zone()
    channel = _channel()
    with timezone.override(tz):
        rows = []
        for post in ScheduledPost.objects.select_related("project"):
            meta = [post.project.display_title if post.project else "Text only", f"{len(post.text)} characters"]
            if post.status == ScheduledPost.Status.POSTED and post.message_id and channel.startswith("@"):
                meta.append(f"t.me/{channel[1:]}/{post.message_id}")
            if post.error:
                meta.append(post.error)
            rows.append({
                "key": timezone.localtime(post.publish_at).strftime("%b %d · %H:%M"),
                "title": post.title,
                "meta": " · ".join(meta),
                "badge": {"label": post.get_status_display(), "tone": BADGES[post.status]},
                "href": reverse("studio:channel_post", args=[post.pk]),
            })
        upcoming = ScheduledPost.objects.filter(status=ScheduledPost.Status.SCHEDULED).count()
        return render(request, "studio/channel.html", {
            "rows": rows,
            "intro": f"Posts for {channel or 'the channel'}, published by the job runner at their time ({tz_name}). {upcoming} waiting.",
        })


@require_http_methods(["GET", "POST"])
def post_edit(request, pk=None):
    post = get_object_or_404(ScheduledPost, pk=pk) if pk else None
    if post and post.status == ScheduledPost.Status.POSTED:
        messages.info(request, "That post is already in the channel. Edit it in Telegram.")
        return redirect("studio:channel")
    tz_name, tz = _zone()
    with timezone.override(tz):
        form = ScheduledPostForm(request.POST or None, instance=post, tz_label=tz_name)
        if request.method == "POST" and form.is_valid():
            saved = form.save(commit=False)
            saved.status, saved.error = ScheduledPost.Status.SCHEDULED, ""
            saved.save()
            messages.success(request, f"Scheduled for {timezone.localtime(saved.publish_at):%b %d, %H:%M} ({tz_name}).")
            return redirect("studio:channel")
        return render(request, "studio/form_page.html", {
            "window_title": f"channel/{post.pk}.txt" if post else "channel/new.txt",
            "heading": "Edit post" if post else "Schedule a post",
            "intro": "The post goes out with its project's screenshot or card unless you give a picture URL.",
            "form": form,
            "wide": True,
            "submit_label": "Schedule",
            "back_url": reverse("studio:channel"),
            "back_label": "Back to the channel",
            "delete_url": reverse("studio:channel_cancel", args=[post.pk]) if post and post.status != ScheduledPost.Status.CANCELLED else None,
            "delete_label": "Cancel this post",
            "delete_note": "Cancelling keeps the text here but stops it from being posted.",
        })


@require_POST
def cancel(request, pk):
    post = get_object_or_404(ScheduledPost, pk=pk)
    if post.status != ScheduledPost.Status.POSTED:
        ScheduledPost.objects.filter(pk=pk).update(status=ScheduledPost.Status.CANCELLED)
        messages.success(request, "Cancelled. It won't be posted.")
    return redirect("studio:channel")
