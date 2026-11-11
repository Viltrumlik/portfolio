"""Failed background jobs, with a way to queue one again."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from jobs.models import Job


@require_GET
def failed_jobs(request):
    jobs = Job.objects.filter(status=Job.Status.FAILED).order_by("-finished_at", "-pk")[:100]
    return render(request, "studio/jobs.html", {"jobs": jobs})


@require_POST
def retry(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.Status.FAILED)
    Job.objects.filter(pk=job.pk, status=Job.Status.FAILED).update(
        status=Job.Status.QUEUED, attempts=0, run_at=timezone.now(), finished_at=None, locked_at=None,
    )
    messages.success(request, f"{job.kind} queued again. It runs within a minute.")
    return redirect("studio:jobs")
