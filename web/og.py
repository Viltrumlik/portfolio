"""Open Graph images in the Atlas style: a cream window with a lime title bar on the graphite desk.

Images are cached under MEDIA_ROOT/og/<kind>/<slug>-<digest>.png; the digest covers the text,
so editing a title produces a new image and the old one is removed.
"""
import hashlib
import os
import re
import tempfile
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 630
GRAPHITE = (12, 13, 15)
DESK_DOT = (31, 34, 38)
CREAM = (255, 253, 247)
LIME = (197, 248, 42)
INK = (21, 21, 21)
INK_MUTED = (88, 92, 84)
DESK_INK = (232, 230, 223)
VERSION = "1"

SANS_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]
MONO_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]


def _font(candidates, size, setting):
    for path in [getattr(settings, setting, None), *candidates]:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def _wrap(draw, text, font, max_width, max_lines):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;:") + "…"
    return lines


def render(title, subtitle="", label="about.md", handle=""):
    img = Image.new("RGB", (WIDTH, HEIGHT), GRAPHITE)
    draw = ImageDraw.Draw(img)
    for x in range(9, WIDTH, 18):
        for y in range(9, HEIGHT, 18):
            draw.point((x, y), fill=DESK_DOT)

    left, top, right, bottom = 80, 70, 1110, 520
    draw.rectangle((left + 10, top + 10, right + 10, bottom + 10), fill=(0, 0, 0))  # hard offset shadow
    draw.rectangle((left, top, right, bottom), fill=CREAM, outline=INK, width=3)
    bar = 56
    draw.rectangle((left + 3, top + 3, right - 3, top + bar), fill=LIME)
    draw.line((left, top + bar, right, top + bar), fill=INK, width=3)
    for i in range(3):
        cx = left + 30 + i * 26
        draw.ellipse((cx - 8, top + bar // 2 - 7, cx + 8, top + bar // 2 + 9), outline=INK, width=2)
    mono = _font(MONO_FONTS, 24, "ATLAS_OG_MONO_FONT")
    draw.text((left + 120, top + bar // 2 + 1), label, font=mono, fill=INK, anchor="lm")

    body_w = right - left - 120
    for size, max_lines in ((72, 2), (60, 3), (48, 3)):
        font = _font(SANS_FONTS, size, "ATLAS_OG_FONT")
        lines = _wrap(draw, title, font, body_w, max_lines)
        if len(lines) <= max_lines and all(draw.textlength(ln, font=font) <= body_w for ln in lines):
            break
    y = top + bar + 50
    for line in lines:
        draw.text((left + 60, y), line, font=font, fill=INK)
        y += int(size * 1.15)
    if subtitle:
        small = _font(SANS_FONTS, 30, "ATLAS_OG_FONT")
        for line in _wrap(draw, subtitle, small, body_w, 2):
            if y + 40 > bottom - 20:
                break
            y += 14
            draw.text((left + 60, y), line, font=small, fill=INK_MUTED)
            y += 30

    draw.rectangle((left, 566, left + 16, 582), fill=LIME)
    if handle:
        draw.text((left + 30, 574), handle, font=_font(MONO_FONTS, 24, "ATLAS_OG_MONO_FONT"), fill=DESK_INK, anchor="lm")
    return img


def image_path(kind, slug, title, subtitle="", label="about.md", handle=""):
    """Path to the cached PNG, generating it (and removing stale versions) when missing."""
    digest = hashlib.sha256("\n".join([VERSION, title, subtitle, label, handle]).encode()).hexdigest()[:10]
    folder = Path(settings.MEDIA_ROOT) / "og" / kind
    path = folder / f"{slug}-{digest}.png"
    if path.exists():
        return path
    folder.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            render(title, subtitle, label, handle).save(fh, "PNG", optimize=True)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    stale = re.compile(rf"^{re.escape(slug)}-[0-9a-f]{{10}}\.png$")
    for old in folder.iterdir():
        if old != path and stale.match(old.name):
            old.unlink(missing_ok=True)
    return path
