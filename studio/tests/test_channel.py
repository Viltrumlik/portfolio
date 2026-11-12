"""The studio's channel queue: list, schedule, edit in the owner's time zone, cancel."""
import datetime as dt

import pytest
from django.utils import timezone

from automations.models import ScheduledPost
from content.models import Profile, Project

pytestmark = pytest.mark.django_db


def html(response, status=200):
    assert response.status_code == status, response.status_code
    return response.content.decode()


def test_channel_lists_the_queue_in_order(staff):
    ScheduledPost.objects.create(text="Second post\nbody", publish_at=timezone.now() + dt.timedelta(days=4))
    ScheduledPost.objects.create(text="First post\nbody", publish_at=timezone.now() + dt.timedelta(days=2))
    page = html(staff.get("/studio/channel/"))
    assert page.index("First post") < page.index("Second post")
    assert ">Channel<" in page


def test_scheduling_a_post_reads_the_time_in_the_owners_zone(staff):
    Profile.objects.update_or_create(pk=1, defaults={"timezone": "Asia/Tashkent"})
    project = Project.objects.create(repo_full_name="V/mars", slug="mars")
    r = staff.post("/studio/channel/new/", {"text": "Zero to Mars\n\nProblem…", "project": project.pk,
                                             "image_url": "", "publish_at": "2026-11-20T19:00"})
    assert r.status_code == 302
    p = ScheduledPost.objects.get()
    assert p.publish_at == dt.datetime(2026, 11, 20, 14, 0, tzinfo=dt.timezone.utc)  # 19:00 in Tashkent
    assert (p.status, p.project) == ("scheduled", project)
    page = html(staff.get(f"/studio/channel/{p.pk}/"))
    assert 'value="2026-11-20T19:00"' in page


def test_a_caption_over_telegrams_limit_is_refused_when_it_has_a_picture(staff):
    project = Project.objects.create(repo_full_name="V/mars", slug="mars")
    r = staff.post("/studio/channel/new/", {"text": "x" * 1100, "project": project.pk, "image_url": "", "publish_at": "2026-11-20T19:00"})
    assert r.status_code == 200 and "1024" in r.content.decode()
    assert not ScheduledPost.objects.exists()


def test_cancelling_keeps_the_post_but_stops_it(staff):
    p = ScheduledPost.objects.create(text="Later", publish_at=timezone.now() + dt.timedelta(days=2))
    r = staff.post(f"/studio/channel/{p.pk}/cancel/")
    assert r.status_code == 302
    p.refresh_from_db()
    assert p.status == "cancelled"
