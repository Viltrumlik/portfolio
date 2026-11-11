"""Turn stored text (Markdown, or HTML migrated from the old site) into safe HTML.

Everything shown to visitors goes through `sanitize_html`, so templates may mark
the result safe. Never mark raw model text safe.
"""
import re
from html import unescape

import bleach
import markdown as md_lib
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

ALLOWED_TAGS = {
    "p", "a", "ul", "ol", "li", "strong", "em", "code", "pre", "blockquote",
    "h2", "h3", "h4", "img", "hr", "br",
    "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {"a": ["href", "title"], "img": ["src", "alt"], "th": ["align"], "td": ["align"]}
ALLOWED_PROTOCOLS = {"http", "https", "mailto"}
MARKDOWN_EXTENSIONS = ["fenced_code", "tables", "sane_lists"]

_DROP_WITH_CONTENT = re.compile(r"<(script|style|iframe|object|embed|template)\b.*?</\1\s*>", re.I | re.S)


def sanitize_html(html):
    """Keep only the allowlisted tags and attributes. Dangerous elements are dropped with their content."""
    html = _DROP_WITH_CONTENT.sub("", html or "")
    cleaned = bleach.clean(
        html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols=ALLOWED_PROTOCOLS, strip=True,
        strip_comments=True,
    )
    return mark_safe(cleaned.strip())


def render_markdown(text):
    return sanitize_html(md_lib.markdown(text or "", extensions=MARKDOWN_EXTENSIONS, output_format="html"))


def render_body(text, body_format="markdown"):
    """Render a Post body or any Markdown field by its format ("markdown" or "html")."""
    if body_format == "html":
        return sanitize_html(text)
    return render_markdown(text)


def plain_text(text, body_format="markdown"):
    return unescape(strip_tags(render_body(text, body_format))).strip()


def excerpt(text, words=40, body_format="markdown"):
    """Plain text of the first paragraph, cut to `words` words."""
    html = render_body(text, body_format)
    first = re.split(r"</p>|</h[2-4]>|</li>|<br>", html, maxsplit=1)[0] if html else ""
    plain = re.sub(r"\s+", " ", unescape(strip_tags(first))).strip()
    parts = plain.split(" ")
    if len(parts) > words:
        return " ".join(parts[:words]).rstrip(",.;:") + "…"
    return plain
