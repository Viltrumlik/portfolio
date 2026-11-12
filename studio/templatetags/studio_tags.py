"""Studio chrome: {% load studio_tags %} then {% studio_menubar %}."""
from django import template
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from automations.models import ScheduledPost
from jobs.models import Job
from web import components as c
from web.models import ContactMessage

register = template.Library()


def _nav(path):
    """(label, href, active, count) for each studio section."""
    inbox = ContactMessage.objects.filter(is_read=False).count()
    failed = Job.objects.filter(status=Job.Status.FAILED).count()
    desk = reverse("studio:desk")
    return [
        ("Desk", desk, path == desk or path.startswith(desk + "connections/"), 0),
        ("Automations", reverse("studio:automations"), path.startswith((reverse("studio:automations"), reverse("studio:webhooks"))), 0),
        ("Content", reverse("studio:content"), path.startswith(reverse("studio:content")), 0),
        ("Channel", reverse("studio:channel"), path.startswith(reverse("studio:channel")),
         ScheduledPost.objects.filter(status=ScheduledPost.Status.SCHEDULED).count()),
        ("Inbox", reverse("studio:inbox"), path.startswith(reverse("studio:inbox")), inbox),
        ("Jobs", reverse("studio:jobs"), path.startswith(reverse("studio:jobs")), failed),
    ]


@register.simple_tag(takes_context=True)
def studio_menubar(context):
    request = context["request"]
    links = []
    for label, href, active, count in _nav(request.path):
        count_html = format_html(' <span class="st-count">{}</span>', count) if count else ""
        if active:
            links.append(format_html('<a href="{}" class="at-menubar__link is-active" aria-current="page"><span>{}</span>{}</a>', href, label, count_html))
        else:
            links.append(format_html('<a href="{}" class="at-menubar__link"><span>{}</span>{}</a>', href, label, count_html))
    logout = format_html(
        '<form method="post" action="{}" class="st-logout"><input type="hidden" name="csrfmiddlewaretoken" value="{}">'
        '<button type="submit" class="at-menubar__link">Log out</button></form>',
        reverse("studio:logout"), get_token(request),
    )
    return format_html(
        '<header class="at-menubar"><a class="at-menubar__brand" href="{}"><span class="at-menubar__logo" aria-hidden="true"></span>studio</a>'
        '<nav class="at-menubar__nav" aria-label="Studio">{}</nav><div class="at-menubar__end">'
        '<a href="/" class="at-menubar__link">View site</a>{}'
        '<button type="button" class="at-menubar__cmd" aria-label="Open command palette" data-cmdk-open>{}</button></div></header>',
        reverse("studio:desk"), mark_safe("".join(links)), logout, c.kbd("⌘K"),
    )

