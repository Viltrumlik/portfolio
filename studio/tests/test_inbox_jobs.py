"""Inbox (contact messages) and failed jobs."""
import pytest
from django.utils import timezone

from jobs.models import Job
from web.models import ContactMessage

pytestmark = pytest.mark.django_db


def html(response, status=200):
    assert response.status_code == status, response.status_code
    return response.content.decode()


# --- inbox ----------------------------------------------------------------------------


def test_inbox_lists_messages_newest_first_with_unread_marked(staff):
    ContactMessage.objects.create(name="Dana", email="dana@example.com", message="First <b>hi</b>", is_read=True)
    ContactMessage.objects.create(name="Bobur", email="bobur@example.com", message="Second\nline two")
    page = html(staff.get("/studio/inbox/"))
    assert page.index("Bobur") < page.index("Dana")
    assert "<b>hi</b>" not in page and "First &lt;b&gt;hi&lt;/b&gt;" in page
    assert "Unread" in page and 'href="mailto:bobur@example.com"' in page
    assert '<span class="st-count">1</span>' in page  # the menu bar's unread count


def test_mark_read(staff):
    msg = ContactMessage.objects.create(name="Dana", email="dana@example.com", message="Hi")
    r = staff.post(f"/studio/inbox/{msg.pk}/read/")
    assert r.status_code == 302 and r["Location"] == "/studio/inbox/"
    msg.refresh_from_db()
    assert msg.is_read is True


def test_delete_message(staff):
    msg = ContactMessage.objects.create(name="Dana", email="dana@example.com", message="Hi")
    r = staff.post(f"/studio/inbox/{msg.pk}/delete/")
    assert r.status_code == 302 and r["Location"] == "/studio/inbox/"
    assert not ContactMessage.objects.exists()


def test_empty_inbox(staff):
    assert "No messages yet." in html(staff.get("/studio/inbox/"))


# --- jobs -----------------------------------------------------------------------------


def test_jobs_lists_failed_jobs_only(staff):
    Job.objects.create(kind="lastfm.poll", status="failed", attempts=5, last_error="Last.fm could not be reached.", finished_at=timezone.now())
    Job.objects.create(kind="github.sync", status="done", finished_at=timezone.now())
    page = html(staff.get("/studio/jobs/"))
    assert "lastfm.poll" in page and "Last.fm could not be reached." in page and "5 attempts" in page
    assert "github.sync" not in page
    assert "Retry" in page


def test_retry_requeues_a_failed_job(staff):
    job = Job.objects.create(kind="lastfm.poll", status="failed", attempts=5, last_error="down", finished_at=timezone.now(),
                             run_at=timezone.now() - timezone.timedelta(days=1))
    before = timezone.now()
    r = staff.post(f"/studio/jobs/{job.pk}/retry/")
    assert r.status_code == 302 and r["Location"] == "/studio/jobs/"
    job.refresh_from_db()
    assert (job.status, job.attempts, job.finished_at, job.locked_at) == ("queued", 0, None, None)
    assert job.run_at >= before
    assert "lastfm.poll queued again" in html(staff.get("/studio/jobs/"))


def test_only_failed_jobs_can_be_retried(staff):
    job = Job.objects.create(kind="github.sync", status="running")
    assert staff.post(f"/studio/jobs/{job.pk}/retry/").status_code == 404
    job.refresh_from_db()
    assert job.status == "running"


def test_no_failed_jobs(staff):
    assert "No failed jobs." in html(staff.get("/studio/jobs/"))
