"""Outgoing webhooks: signed POSTs to n8n, Make or Zapier. The secret is write-only."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from integrations import actions
from integrations.crypto import mask
from integrations.errors import IntegrationError
from integrations.models import OutboundHook
from web import live

from ..forms import WebhookForm
from .common import safe_next


def _rows():
    return [
        {
            "hook": hook,
            "secret": mask((hook.secret or {}).get("secret", "")),
            "last": f"{hook.last_status_code or 'no answer'} · {live.relative(hook.last_delivery_at)}" if hook.last_delivery_at else "",
        }
        for hook in OutboundHook.objects.order_by("name", "pk")
    ]


@require_http_methods(["GET", "POST"])
def webhook_list(request):
    form = WebhookForm(request.POST or None, initial={"is_active": True})
    if request.method == "POST" and form.is_valid():
        hook = form.save()
        messages.success(request, f"Webhook “{hook.name}” saved. Send a test to check it.")
        return redirect("studio:webhooks")
    return render(request, "studio/webhooks.html", {"rows": _rows(), "form": form})


@require_http_methods(["GET", "POST"])
def webhook_edit(request, pk):
    hook = get_object_or_404(OutboundHook, pk=pk)
    form = WebhookForm(request.POST or None, instance=hook)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Webhook “{hook.name}” saved.")
        return redirect("studio:webhooks")
    return render(request, "studio/webhook_edit.html", {"hook": hook, "form": form})


@require_POST
def webhook_test(request, pk):
    hook = get_object_or_404(OutboundHook, pk=pk)
    try:
        status = actions.send_test(hook)
    except IntegrationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"“{hook.name}” answered {status}.")
    return redirect(safe_next(request, reverse("studio:webhooks")))


@require_POST
def webhook_delete(request, pk):
    hook = get_object_or_404(OutboundHook, pk=pk)
    hook.delete()
    messages.success(request, f"Webhook “{hook.name}” deleted.")
    return redirect("studio:webhooks")
