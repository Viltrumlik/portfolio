"""Atlas components as server-rendered HTML.

Each function returns SafeString markup identical to the reference React bundle
(frontend/atlas-reference/bundle.js), so the shared stylesheet styles both.
Every value is escaped; only arguments that are already SafeString pass through.
"""
from django.utils.html import conditional_escape, format_html, format_html_join
from django.utils.safestring import mark_safe

# Atlas glyphs: 24px grid, 1.5 stroke, round caps. Strings are paths; ("c", cx, cy, r) circles; ("p", points) polygons.
ICONS = {
    "arrow-up-right": ["M7 17 17 7", "M8 7h9v9"],
    "arrow-right": ["M4 12h15", "M13 6l6 6-6 6"],
    "check": ["M5 12.5l4.5 4.5L19 7.5"],
    "x": ["M6 6l12 12", "M18 6 6 18"],
    "plus": ["M12 5v14", "M5 12h14"],
    "search": [("c", 10.5, 10.5, 6.5), "M15.5 15.5 20.5 20.5"],
    "refresh": ["M20 12a8 8 0 1 1-8-8c2.2 0 4.2.9 5.65 2.35L20 8.5", "M20 4v4.5h-4.5"],
    "link": ["M9.5 14.5l5-5", "M11 6.5l1.5-1.5a4.24 4.24 0 0 1 6 6L17 12.5", "M13 17.5 11.5 19a4.24 4.24 0 0 1-6-6L7 11.5"],
    "star": [("p", "12 3.5 14.6 9 20.5 9.6 16 13.6 17.3 19.5 12 16.5 6.7 19.5 8 13.6 3.5 9.6 9.4 9")],
    "fork": [("c", 6, 5, 2), ("c", 18, 5, 2), ("c", 12, 19, 2), "M6 7v1.5a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V7", "M12 11.5V17"],
    "commit": [("c", 12, 12, 3.5), "M3 12h5.5", "M15.5 12H21"],
    "clock": [("c", 12, 12, 8.5), "M12 7.5V12l3 2"],
    "alert": [("c", 12, 12, 8.5), "M12 7.5v5", "M12 16.25v.5"],
    "zap": ["M13 3 5 13.5h6.5L10.5 21 19 10.5h-6.5L13 3z"],
    "music": ["M9 18V6l10-2v12", ("c", 6.5, 18, 2.5), ("c", 16.5, 16, 2.5)],
    "code": ["M8.5 7 3.5 12l5 5", "M15.5 7l5 5-5 5"],
    "pin": ["M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z", ("c", 12, 10, 2.25)],
    "power": ["M12 3.5v8", "M6.5 6.5a7.5 7.5 0 1 0 11 0"],
}

SERVICES = {
    "GH": "GitHub", "WK": "WakaTime", "LF": "Last.fm", "TG": "Telegram",
    "WH": "Outgoing webhook", "RS": "RSS", "ST": "This site",
}


def _num(v):
    return format(v, "g") if isinstance(v, float) else str(v)


def _classes(*names):
    return " ".join(n for n in names if n)


def data_attrs(attrs):
    """Render {"data_island": "now", "data_theme_toggle": True} as ` data-island="now" data-theme-toggle`."""
    out = []
    for key, value in (attrs or {}).items():
        if value is None or value is False:
            continue
        name = key.replace("_", "-")
        if value is True:
            out.append(format_html(" {}", name))
        else:
            out.append(format_html(' {}="{}"', name, value))
    return mark_safe("".join(out))


def icon(name, size=16, title=None, cls=None, stroke_width=1.5):
    shapes = ICONS.get(name)
    if not shapes:
        return ""
    parts = []
    for d in shapes:
        if isinstance(d, str):
            parts.append(format_html('<path d="{}"/>', d))
        elif d[0] == "c":
            parts.append(format_html('<circle cx="{}" cy="{}" r="{}"/>', _num(d[1]), _num(d[2]), _num(d[3])))
        else:
            parts.append(format_html('<polygon points="{}"/>', d[1]))
    a11y = format_html(' role="img" aria-label="{}"', title) if title else mark_safe(' aria-hidden="true"')
    return format_html(
        '<svg class="{}" width="{}" height="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="{}" stroke-linecap="round" stroke-linejoin="round"{}>{}</svg>',
        _classes("at-icon", cls), size, size, _num(stroke_width), a11y, mark_safe("".join(parts)),
    )


def badge(label, tone="neutral", dot=False, pulse=False, icon_name=None):
    dot_html = format_html('<span class="{}" aria-hidden="true"></span>', _classes("at-badge__dot", pulse and "is-pulse")) if dot else ""
    glyph = icon(icon_name, size=12) if icon_name else ""
    return format_html('<span class="at-badge at-badge--{}">{}{}{}</span>', tone or "neutral", dot_html, glyph, label)


def button(label=None, href=None, variant="secondary", size="md", icon_name=None, icon_right=None, type="button",
           cls=None, aria_label=None, attrs=None):
    icon_size = 14 if size == "sm" else 16
    has_label = label not in (None, "", False)
    classes = _classes("at-btn", f"at-btn--{variant or 'secondary'}", size == "sm" and "at-btn--sm",
                       not has_label and "at-btn--icon", cls)
    inner = mark_safe("".join([
        icon(icon_name, icon_size) if icon_name else "",
        format_html("<span>{}</span>", label) if has_label else "",
        icon(icon_right, icon_size) if icon_right else "",
    ]))
    extra = data_attrs({"aria_label": aria_label, **(attrs or {})})
    if href:
        return format_html('<a href="{}" class="{}"{}>{}</a>', href, classes, extra, inner)
    return format_html('<button type="{}" class="{}"{}>{}</button>', type or "button", classes, extra, inner)


def kbd(key):
    return format_html('<kbd class="at-kbd">{}</kbd>', key)


def service_code(code, label=None, size="md"):
    if label:
        return format_html('<span class="at-code at-code--{}" role="img" aria-label="{}" title="{}">{}</span>', size, label, label, code)
    return format_html('<span class="at-code at-code--{}" aria-hidden="true">{}</span>', size, code)


def _length(v):
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().lstrip("-").replace(".", "", 1).isdigit()):
        return f"{_num(v) if not isinstance(v, str) else v.strip()}px"
    return str(v)


def window_open(title, active=False, id=None, x=None, y=None, w=None, label=None, cls=None, bar_end=None,
                delay=None, attrs=None, h=None):
    style = []
    if x not in (None, ""):
        style.append(f"--x:{_length(x)}")
    if y not in (None, ""):
        style.append(f"--y:{_length(y)}")
    if w not in (None, ""):
        style.append(f"--w:{_length(w)}")
    if h not in (None, ""):
        style.append(f"--h:{_length(h)}")
    if delay not in (None, ""):
        style.append(f"--delay:{_num(delay)}ms")
    head = format_html(
        '<section class="{}"{}{}{}{}>',
        _classes("at-win", active and "is-active", cls),
        format_html(' data-win="{}"', id) if id else "",
        format_html(' aria-label="{}"', label or title),
        format_html(' style="{}"', ";".join(style)) if style else "",
        data_attrs(attrs),
    )
    end = format_html('<span class="at-win__end">{}</span>', bar_end) if bar_end not in (None, "") else ""
    bar = format_html(
        '<div class="at-win__bar"><span class="at-win__ctl" aria-hidden="true"><i></i><i></i><i></i></span>'
        '<span class="at-win__title">{}</span>{}</div>',
        title, end,
    )
    return head + bar


def window(title, body="", body_cls=None, **kwargs):
    return window_open(title, **kwargs) + format_html(
        '<div class="{}">{}</div></section>', _classes("at-win__body", body_cls), conditional_escape(body)
    )


def section_header(title, index=None, kicker=None, action=None):
    meta = mark_safe(
        (format_html('<span class="at-section__index">{}</span>', index) if index else "")
        + (format_html('<span class="at-section__kicker">{}</span>', kicker) if kicker else "")
    )
    return format_html(
        '<header class="at-section"><div class="at-section__meta">{}</div><div class="at-section__row">'
        '<h2 class="at-section__title" data-island="decode">{}</h2>{}</div></header>',
        meta, title, action or "",
    )


def stat(value, label, unit=None, delta=None, trend=None):
    return format_html(
        '<div class="at-stat"><div class="at-stat__value">{}{}</div><div class="at-stat__label">{}</div>{}</div>',
        value,
        format_html('<span class="at-stat__unit">{}</span>', unit) if unit else "",
        label,
        format_html('<div class="{}">{}</div>', _classes("at-stat__delta", trend == "down" and "is-down"), delta) if delta else "",
    )


def dock(items, label="Dock"):
    rows = []
    for it in items:
        cls = _classes("at-dock__item", it.get("active") and "is-active")
        if it.get("href"):
            rows.append(format_html('<a href="{}" class="{}" title="{}" aria-label="{}">{}</a>',
                                    it["href"], cls, it["label"], it["label"], it["code"]))
        else:
            rows.append(format_html('<button type="button" class="{}" title="{}" aria-label="{}"{}>{}</button>',
                                    cls, it["label"], it["label"], data_attrs(it.get("attrs")), it["code"]))
    return format_html('<nav class="at-dock" aria-label="{}">{}</nav>', label, mark_safe("".join(rows)))


def project_row(title, index=None, summary=None, stack=(), meta=None, href=None, status=None):
    index_text = f"{index:02d}" if isinstance(index, int) else (index or "")
    status_html = badge(status["label"], status.get("tone", "neutral"), status.get("dot")) if status else ""
    main = format_html(
        '<span class="at-prow__main"><span class="at-prow__title">{}{}</span>{}</span>',
        title, status_html,
        format_html('<span class="at-prow__summary">{}</span>', summary) if summary else "",
    )
    year = format_html('<span class="at-prow__year">{}{}</span>', meta if meta is not None else "",
                       icon("arrow-up-right", 16) if href else "")
    inner = format_html('<span class="at-prow__index">{}</span>{}<span class="at-prow__stack">{}</span>{}',
                        index_text, main, " · ".join(str(s) for s in (stack or [])), year)
    if href:
        return format_html('<a class="at-prow" href="{}">{}</a>', href, inner)
    return format_html('<div class="at-prow">{}</div>', inner)


def repo_card(name, owner=None, description=None, language=None, stars=0, forks=0, updated=None, pinned=False, href=None):
    head = format_html(
        '<div class="at-repo__head"><span class="at-repo__name">{}{}</span>{}</div>',
        format_html('<span class="at-repo__owner">{}/</span>', owner) if owner else "",
        name,
        badge("Pinned") if pinned else "",
    )
    meta = format_html(
        '<div class="at-repo__meta">{}<span>{}{}<span class="at-sr"> stars</span></span>'
        '<span>{}{}<span class="at-sr"> forks</span></span>{}</div>',
        format_html('<span class="at-repo__lang"><i aria-hidden="true"></i>{}</span>', language) if language else "",
        icon("star", 14), stars or 0, icon("fork", 14), forks or 0,
        format_html('<span class="at-repo__updated">{}</span>', updated) if updated else "",
    )
    inner = head + (format_html('<p class="at-repo__desc">{}</p>', description) if description else "") + meta
    if href:
        return format_html('<a class="at-repo" href="{}">{}</a>', href, inner)
    return format_html('<div class="at-repo">{}</div>', inner)


def activity_feed(items, label="Activity"):
    if not items:
        return ""
    rows = []
    for it in items:
        danger = it.get("tone") == "danger"
        rows.append(format_html(
            '<li class="{}"><time class="at-feed__time" datetime="{}">{}</time>{}<span class="at-feed__text">{}{}{}</span></li>',
            _classes("at-feed__row", danger and "is-danger"),
            it.get("datetime", ""), it.get("time", ""),
            service_code(it.get("code", ""), it.get("source"), "sm"),
            icon("alert", 14, title="Failed") if danger else "",
            it.get("text", ""),
            format_html('<span class="at-feed__meta">{}</span>', it["meta"]) if it.get("meta") else "",
        ))
    return format_html('<ol class="at-feed" aria-label="{}">{}</ol>', label, mark_safe("".join(rows)))


def contribution_graph(days, label="contributions in the last six months", total=None, cell=11, gap=3):
    """`days` is a list of (date, count), oldest first, starting on a Sunday."""
    if not days:
        return ""
    peak = max([c for _, c in days] + [1])

    def level(c):
        if c <= 0:
            return 0
        if c <= peak * 0.25:
            return 1
        if c <= peak * 0.5:
            return 2
        if c <= peak * 0.75:
            return 3
        return 4

    cols = -(-len(days) // 7)
    width = cols * (cell + gap) - gap
    height = 7 * (cell + gap) - gap
    total = sum(c for _, c in days) if total is None else total
    cells = format_html_join(
        "",
        '<rect x="{}" y="{}" width="{}" height="{}" rx="2" class="at-graph__cell at-heat-{}"><title>{}</title></rect>',
        (
            (
                (i // 7) * (cell + gap), (i % 7) * (cell + gap), cell, cell, level(c),
                f"{c} contribution{'' if c == 1 else 's'} on {d:%b} {d.day}, {d.year}",
            )
            for i, (d, c) in enumerate(days)
        ),
    )
    legend = format_html_join("", '<i class="at-heat-{}"></i>', ((n,) for n in range(5)))
    return format_html(
        '<figure class="at-graph"><div class="at-graph__scroll">'
        '<svg width="{}" height="{}" viewBox="0 0 {} {}" role="img" aria-label="{} {}">{}</svg></div>'
        '<figcaption class="at-graph__caption"><span><strong>{}</strong> {}</span>'
        '<span class="at-graph__legend" aria-hidden="true">Less{}More</span></figcaption></figure>',
        width, height, width, height, total, label, cells, f"{total:,}", label, legend,
    )
