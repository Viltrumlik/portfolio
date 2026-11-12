"""Atlas components for server-rendered templates: {% load atlas %}.

Block tags:   {% window title="about.md" active=True id="about" x="3%" y=20 w="46%" %}…{% endwindow %}
              {% desk height=520 %}…{% enddesk %}
Simple tags:  icon, badge, button, kbd, service_code, section_header, stat, dock, project_row, repo_card,
              contribution_graph, activity_feed, menubar, now_window, clock, cmdk_data
"""
from django import template
from django.template.base import token_kwargs
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from content.models import Profile

from .. import components as c
from .. import live
from ..site import NAV_LINKS, command_palette

register = template.Library()


def _profile(context):
    profile = context.get("profile")
    return profile if isinstance(profile, Profile) else Profile.load()


def _split_attrs(values):
    """Pull data_*/aria_* kwargs out as HTML attributes."""
    return {k: values.pop(k) for k in list(values) if k.startswith(("data_", "aria_"))}


# --- block tags --------------------------------------------------------------------------


class WindowNode(template.Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        values = {k: v.resolve(context) for k, v in self.kwargs.items()}
        attrs = _split_attrs(values)
        body_cls = values.pop("body_cls", None)
        body = mark_safe(self.nodelist.render(context))
        return c.window_open(attrs=attrs, **values) + format_html(
            '<div class="{}">{}</div></section>', "at-win__body" + (f" {body_cls}" if body_cls else ""), body
        )


@register.tag("window")
def do_window(parser, token):
    """A window: title (required), active, id, x, y, w, label, cls, body_cls, bar_end, delay, data_*=…"""
    bits = token.split_contents()
    name, bits = bits[0], bits[1:]
    kwargs = token_kwargs(bits, parser, support_legacy=False)
    if bits:
        raise template.TemplateSyntaxError(f"{name} takes only key=value arguments")
    if "title" not in kwargs:
        raise template.TemplateSyntaxError(f"{name} needs a title")
    nodelist = parser.parse(("endwindow",))
    parser.delete_first_token()
    return WindowNode(nodelist, kwargs)


class DeskNode(template.Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        values = {k: v.resolve(context) for k, v in self.kwargs.items()}
        height = values.get("height") or 520
        return format_html(
            '<div class="at-desk" data-island="desk" style="--desk-h:{}px"{}>{}</div>',
            height, format_html(' aria-label="{}"', values["label"]) if values.get("label") else "",
            mark_safe(self.nodelist.render(context)),
        )


@register.tag("desk")
def do_desk(parser, token):
    """The dotted desk the hero windows sit on: {% desk height=520 %}…windows… {% dock … %}{% enddesk %}"""
    bits = token.split_contents()[1:]
    kwargs = token_kwargs(bits, parser, support_legacy=False)
    nodelist = parser.parse(("enddesk",))
    parser.delete_first_token()
    return DeskNode(nodelist, kwargs)


# --- primitives --------------------------------------------------------------------------


@register.simple_tag
def icon(name, size=16, title=None, cls=None):
    return c.icon(name, size=size, title=title, cls=cls)


@register.simple_tag
def badge(label, tone="neutral", dot=False, pulse=False, icon=None):
    return c.badge(label, tone=tone, dot=dot, pulse=pulse, icon_name=icon)


@register.simple_tag(name="button")
def button_tag(label=None, **kwargs):
    """{% button "Download CV" href=… variant="primary|secondary|ghost" size="sm" icon=… icon_right=… type="submit" %}"""
    attrs = _split_attrs(kwargs)
    kwargs["icon_name"] = kwargs.pop("icon", None)
    return c.button(label, attrs=attrs, **kwargs)


@register.simple_tag
def kbd(key):
    return c.kbd(key)


@register.simple_tag
def service_code(code, label=None, size="md"):
    return c.service_code(code, label=label, size=size)


@register.simple_tag
def section_header(title, index=None, kicker=None, action_label=None, action_href=None):
    action = c.button(action_label, href=action_href, variant="ghost", size="sm", icon_right="arrow-right") if action_label and action_href else None
    return c.section_header(title, index=index, kicker=kicker, action=action)


@register.simple_tag
def stat(value, label, unit=None, delta=None, trend=None):
    return c.stat(value, label, unit=unit, delta=delta, trend=trend)


@register.simple_tag
def dock(items, label="Dock"):
    return c.dock(items or [], label=label)


@register.simple_tag
def clock(tz=None, fmt="HH:MM"):
    now = live.local_now(tz)
    text = f"{now:%H:%M:%S}" if fmt == "HH:MM:SS" else f"{now:%H:%M}"
    return format_html('<time data-island="clock" data-tz="{}" data-format="{}">{}</time>', tz or "UTC", fmt, text)


# --- data components ---------------------------------------------------------------------


@register.simple_tag
def project_row(project=None, **kwargs):
    """{% project_row project index=1 %} or {% project_row title=… summary=… stack=… meta=… href=… index=… %}"""
    values = {}
    if project is not None:
        repo = project.repo
        values = {
            "title": project.display_title,
            "summary": project.summary or (repo.description if repo else ""),
            "stack": project.stack or ([repo.language] if repo and repo.language else []),
            "meta": project.kind or (str(project.created_at.year) if project.created_at else ""),
            "href": reverse("web:project", args=[project.slug]),
            "image": project.image_url,
        }
        if repo and repo.is_archived:
            values["status"] = {"label": "Archived", "tone": "neutral"}
    values.update(kwargs)
    return c.project_row(**values)


@register.simple_tag
def repo_card(repo, href=None, pinned=None):
    owner, _, name = repo.full_name.rpartition("/")
    return c.repo_card(
        name=name or repo.name, owner=owner or None, description=repo.description, language=repo.language,
        stars=repo.stars, forks=repo.forks, updated=live.relative(repo.pushed_at),
        pinned=repo.pinned if pinned is None else pinned, href=href or repo.url,
    )


@register.simple_tag
def contribution_graph(weeks=26, label=None):
    """The GitHub calendar from synced ContributionDay rows; renders nothing when there are none."""
    return c.contribution_graph(live.contribution_days(weeks), label=label or live.graph_label(weeks))


@register.simple_tag(takes_context=True)
def activity_feed(context, events, label="Activity"):
    tz = _profile(context).timezone
    items = [e if isinstance(e, dict) else live.event_item(e, tz) for e in (events or [])]
    return c.activity_feed(items, label=label)


# --- site chrome -------------------------------------------------------------------------


@register.simple_tag(takes_context=True)
def menubar(context):
    profile = _profile(context)
    request = context.get("request")
    path = request.path if request is not None else "/"
    links = mark_safe("".join(
        format_html('<a href="{}" class="at-menubar__link is-active" aria-current="page">{}</a>', href, label)
        if path.startswith(href) else format_html('<a href="{}" class="at-menubar__link">{}</a>', href, label)
        for label, href in NAV_LINKS
    ))
    avail = live.availability(profile)
    status = format_html('<span class="at-menubar__status"><i aria-hidden="true"></i>{}</span>', avail["label"]) if avail["label"] else ""
    city = (profile.location or "").split(",")[0].strip()
    clock_html = format_html('<span class="at-menubar__clock">{}{}</span>', f"{city} " if city else "", clock(profile.timezone))
    return format_html(
        '<header class="at-menubar"><a class="at-menubar__brand" href="/"><span class="at-menubar__logo" aria-hidden="true"></span>{}</a>'
        '<nav class="at-menubar__nav" aria-label="Primary">{}</nav><div class="at-menubar__end">{}{}'
        '<button type="button" class="at-menubar__sound" data-sound-toggle aria-pressed="false"><span data-sound-label>Sound off</span></button>'
        '<button type="button" class="at-menubar__cmd" aria-label="Open command palette" data-cmdk-open>{}</button></div></header>',
        profile.handle or profile.name, links, status, clock_html, c.kbd("⌘K"),
    )


@register.simple_tag(takes_context=True)
def now_window(context, id=None, x=None, y=None, w=None, active=False, title="now.app", delay=None, h=None):
    """The now.app window: local time, availability, location, and the current track (if fresh)."""
    profile = _profile(context)
    avail = live.availability(profile)
    head = format_html(
        '<div class="at-now__head"><span class="at-now__clock">{}</span>{}</div>',
        clock(profile.timezone),
        c.badge(avail["label"], tone=avail["tone"], dot=True) if avail["label"] else "",
    )

    def row(key, glyph, main, sub, attrs=""):
        return format_html(
            '<div class="at-now__row"{}><span class="at-now__k">{}{}</span><span class="at-now__v">{}{}</span></div>',
            mark_safe(attrs), c.icon(glyph, 14), key, main, format_html('<span class="at-now__sub">{}</span>', sub) if sub else "",
        )

    place = row("Based in", "pin", profile.location, live.utc_label(profile.timezone)) if profile.location else ""
    music = live.listening_payload(live.current_listening())
    listening = row(
        "Listening", "music",
        format_html('<span data-now-field="track">{}</span>', music["track"] if music else ""),
        format_html('<span data-now-field="artist">{}</span> · <span data-now-field="played">{}</span>',
                    music["artist"] if music else "", music["played"] if music else ""),
        ' data-now-row="listening"' + ("" if music else " hidden"),
    )
    return c.window_open(
        title, active=active, id=id, x=x, y=y, w=w, h=h, label="Now", cls="at-now", delay=delay,
        attrs={"data_island": "now", "data_src": reverse("web:live_now")},
    ) + format_html('<div class="at-win__body">{}{}{}</div></section>', head, place, listening)


@register.simple_tag(takes_context=True)
def cmdk_data(context):
    """<script type="application/json" id="atlas-cmdk"> with the ⌘K groups (pages, projects, writing, actions)."""
    from django.utils.html import json_script

    request = context.get("request")
    user = getattr(request, "user", None)
    return json_script(command_palette(_profile(context), is_staff=bool(user and user.is_staff)), "atlas-cmdk")
