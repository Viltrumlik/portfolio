"""Scheduled channel posts: the queue, the picture each one carries, and what happens when Telegram says no."""
import datetime as dt

import pytest
from django.utils import timezone

from automations import channel
from automations.models import ScheduledPost
from content.models import Project
from integrations.errors import Permanent, Transient
from integrations.models import Connection
from integrations.providers import telegram
from jobs.models import Job

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def site(settings):
    settings.SITE_URL = "https://site.test"


@pytest.fixture
def tg():
    return Connection.objects.create(provider="telegram", status="connected", account="@bot",
                                     credentials={"bot_token": "1:tok"}, config={"chat_id": 5, "channel_id": "@news"})


@pytest.fixture
def sent(monkeypatch):
    posts = []

    def fake(conn, text, photo_url=None):
        posts.append((text, photo_url))
        return {"message_id": 42}

    monkeypatch.setattr(telegram, "post_channel", fake)
    return posts


def post(**fields):
    defaults = {"text": "Deploys that can't hurt the server", "publish_at": timezone.now() - dt.timedelta(minutes=1)}
    return ScheduledPost.objects.create(**{**defaults, **fields})


def run(p):
    channel.publish({"post_id": p.pk})
    p.refresh_from_db()
    return p


# --- the picture ------------------------------------------------------------------------


def test_picture_comes_from_the_explicit_url_first():
    project = Project.objects.create(repo_full_name="V/mars", slug="mars")
    assert post(project=project, image_url="https://cdn.test/a.png").picture_url() == "https://cdn.test/a.png"


def test_picture_falls_back_to_the_projects_card_or_screenshot():
    project = Project.objects.create(repo_full_name="V/mars", slug="mars")
    assert post(project=project).picture_url() == "https://site.test/og/project/mars.png"


def test_hidden_projects_and_plain_posts_have_no_picture():
    hidden = Project.objects.create(repo_full_name="V/secret", slug="secret", hidden=True)
    assert post(project=hidden).picture_url() is None
    assert post().picture_url() is None


# --- the queue --------------------------------------------------------------------------


def test_due_posts_are_queued_once_and_future_ones_wait():
    due = post()
    later = post(publish_at=timezone.now() + dt.timedelta(days=2))
    cancelled = post(status=ScheduledPost.Status.CANCELLED)
    channel.queue_due_posts(timezone.now())
    channel.queue_due_posts(timezone.now())
    assert list(Job.objects.values_list("kind", "payload")) == [("telegram.scheduled_post", {"post_id": due.pk})]
    due.refresh_from_db(); later.refresh_from_db(); cancelled.refresh_from_db()
    assert (due.status, later.status, cancelled.status) == ("queued", "scheduled", "cancelled")


# --- publishing -------------------------------------------------------------------------


def test_publishing_posts_the_escaped_text_with_the_picture(tg, sent):
    project = Project.objects.create(repo_full_name="V/mars", slug="mars")
    p = run(post(text="A <b> & C", project=project, status=ScheduledPost.Status.QUEUED))
    assert sent == [("A &lt;b&gt; &amp; C", "https://site.test/og/project/mars.png")]
    assert (p.status, p.message_id) == ("posted", 42) and p.posted_at is not None


def test_only_queued_posts_are_published(tg, sent):
    p = run(post(status=ScheduledPost.Status.CANCELLED))
    assert sent == [] and p.status == "cancelled"


def test_without_a_telegram_channel_the_post_fails_with_a_reason(sent):
    p = run(post(status=ScheduledPost.Status.QUEUED))
    assert p.status == "failed" and "Telegram" in p.error and sent == []


def test_a_permanent_refusal_marks_the_post_failed(tg, monkeypatch):
    def refuse(conn, text, photo_url=None):
        raise Permanent("Telegram refused: the bot is not an admin of the channel.")

    monkeypatch.setattr(telegram, "post_channel", refuse)
    p = run(post(status=ScheduledPost.Status.QUEUED))
    assert p.status == "failed" and "not an admin" in p.error


def test_a_temporary_error_is_raised_so_the_job_retries(tg, monkeypatch):
    def flaky(conn, text, photo_url=None):
        raise Transient("Telegram is having trouble (502). It will retry.")

    monkeypatch.setattr(telegram, "post_channel", flaky)
    p = post(status=ScheduledPost.Status.QUEUED)
    with pytest.raises(Transient):
        channel.publish({"post_id": p.pk})
    p.refresh_from_db()
    assert p.status == "queued"
