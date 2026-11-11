"""Contact-form messages: read them, mark them read, delete them."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from web.models import ContactMessage


@require_GET
def inbox(request):
    return render(request, "studio/inbox.html", {"items": ContactMessage.objects.order_by("-created_at", "-pk")[:200]})


@require_POST
def mark_read(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    message.is_read = True
    message.save(update_fields=["is_read"])
    return redirect("studio:inbox")


@require_POST
def delete(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    message.delete()
    messages.success(request, f"Message from {message.name} deleted.")
    return redirect("studio:inbox")
