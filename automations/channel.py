"""Scheduled channel posts: a periodic task queues the due ones, a job publishes each through the bot."""
from django.db import transaction
from django.utils import timezone

from integrations.errors import AuthError, Permanent
from integrations.handlers import live_connection
from integrations.providers import telegram
from jobs.queue import enqueue
from jobs.registry import handler, periodic

from .models import ScheduledPost

KIND = "telegram.scheduled_post"


@periodic
def queue_due_posts(now=None):
    """Move every due, scheduled post to the job queue, exactly once."""
    now = now or timezone.now()
    for pk in ScheduledPost.objects.filter(status=ScheduledPost.Status.SCHEDULED, publish_at__lte=now).values_list("pk", flat=True):
        with transaction.atomic():
            if ScheduledPost.objects.filter(pk=pk, status=ScheduledPost.Status.SCHEDULED).update(status=ScheduledPost.Status.QUEUED):
                enqueue(KIND, {"post_id": pk}, dedupe_key=f"scheduled_post:{pk}")


def _fail(post, reason):
    ScheduledPost.objects.filter(pk=post.pk).update(status=ScheduledPost.Status.FAILED, error=reason)


@handler(KIND)
def publish(payload):
    """Post one queued post. Permanent refusals mark it failed; temporary ones raise so the job retries."""
    post = ScheduledPost.objects.select_related("project").filter(pk=(payload or {}).get("post_id")).first()
    if post is None or post.status != ScheduledPost.Status.QUEUED:
        return
    conn = live_connection("telegram")
    if conn is None or not (conn.config or {}).get("channel_id"):
        _fail(post, "Telegram is not connected, or no channel is set on the connection.")
        return
    try:
        result = telegram.post_channel(conn, telegram.escape_html(post.text), photo_url=post.picture_url())
    except (AuthError, Permanent) as exc:
        _fail(post, str(exc))
        return
    message_id = result.get("message_id") if isinstance(result, dict) else None
    ScheduledPost.objects.filter(pk=post.pk).update(
        status=ScheduledPost.Status.POSTED, message_id=message_id, posted_at=timezone.now(), error="")
