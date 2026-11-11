"""Load Vite-built assets: {% vite_asset "src/main.ts" %}.

Reads the build manifest (settings.VITE_MANIFEST_PATH), or points at the dev
server when settings.VITE_DEV_SERVER is set. Renders nothing if neither exists,
so pages still render (unstyled) before the first frontend build.
"""
import json

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()


def _manifest():
    path = settings.VITE_MANIFEST_PATH
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, OSError, ValueError):
        return None


@register.simple_tag
def vite_asset(entry):
    dev = settings.VITE_DEV_SERVER.rstrip("/")
    if dev:
        return format_html(
            '<script type="module" src="{}/@vite/client"></script>\n<script type="module" src="{}/{}"></script>',
            dev, dev, entry,
        )
    manifest = _manifest()
    if not manifest or entry not in manifest:
        return ""
    chunk = manifest[entry]
    css = format_html_join("\n", '<link rel="stylesheet" href="{}">', ((static("dist/" + c),) for c in chunk.get("css", [])))
    js = format_html('<script type="module" src="{}"></script>', static("dist/" + chunk["file"]))
    return mark_safe(f"{css}\n{js}" if css else js)
