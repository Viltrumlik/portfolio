"""Open Graph images in the Atlas v3 Matrix style: a phosphor terminal window over digital rain.

Images are cached under MEDIA_ROOT/og/<kind>/<slug>-<digest>.png; the digest covers the text,
so editing a title produces a new image and the old one is removed. Bump VERSION to redraw them all.
"""
import hashlib
import os
import random
import re
import tempfile
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1200, 630
DESK = (1, 8, 2)
WINDOW = (3, 18, 8)
EDGE = (13, 79, 32)
PHOSPHOR = (0, 255, 65)
PHOSPHOR_DIM = (15, 127, 48)
ON_PHOSPHOR = (0, 26, 7)
INK = (180, 255, 198)
INK_MUTED = (95, 191, 122)
VERSION = "2"

FONTS = Path(__file__).resolve().parent / "fonts"
BOLD_FONTS = [
    FONTS / "JetBrainsMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]
MONO_FONTS = [
    FONTS / "JetBrainsMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]
RAIN_GLYPHS = "01<>=+*:;/|$#{}[]"


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


def _rain(draw, seed):
    """Faint columns of glyphs behind the window, the same for the same text."""
    rng = random.Random(seed)
    font = _font(MONO_FONTS, 18, "ATLAS_OG_MONO_FONT")
    for x in range(14, WIDTH, 26):
        if rng.random() < 0.45:
            continue
        top, length = rng.randrange(-200, HEIGHT), rng.randrange(4, 16)
        for i in range(length):
            y = top + i * 22
            if 0 <= y < HEIGHT:
                fade = (i + 1) / length
                color = tuple(int(c * 0.35 * fade) for c in PHOSPHOR)
                draw.text((x, y), rng.choice(RAIN_GLYPHS), font=font, fill=color)


def render(title, subtitle="", label="about.md", handle=""):
    img = Image.new("RGB", (WIDTH, HEIGHT), DESK)
    _rain(ImageDraw.Draw(img), hashlib.sha256(f"{title}|{label}".encode()).hexdigest())

    left, top, right, bottom = 80, 64, 1120, 536
    bar = 54

    # Bloom: the window outline and title, blurred and added on top.
    glow = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rectangle((left, top, right, bottom), outline=PHOSPHOR, width=6)
    gd.rectangle((left, top, right, top + bar), fill=PHOSPHOR_DIM)

    draw = ImageDraw.Draw(img)
    draw.rectangle((left, top, right, bottom), fill=WINDOW, outline=PHOSPHOR, width=2)
    draw.rectangle((left, top, right, top + bar), fill=PHOSPHOR)
    mono = _font(MONO_FONTS, 22, "ATLAS_OG_MONO_FONT")
    bold_small = _font(BOLD_FONTS, 22, "ATLAS_OG_FONT")
    draw.rectangle((left + 24, top + bar // 2 - 6, left + 36, top + bar // 2 + 6), fill=ON_PHOSPHOR)
    draw.text((left + 52, top + bar // 2 + 1), label.upper(), font=bold_small, fill=ON_PHOSPHOR, anchor="lm")
    for i in range(3):  # [_][□][x] controls, drawn as boxes
        x = right - 34 - i * 30
        draw.rectangle((x - 9, top + bar // 2 - 9, x + 9, top + bar // 2 + 9), outline=ON_PHOSPHOR, width=2)

    body_w = right - left - 120
    for size, max_lines in ((66, 2), (56, 3), (46, 3)):
        font = _font(BOLD_FONTS, size, "ATLAS_OG_FONT")
        lines = _wrap(draw, title, font, body_w, max_lines)
        if len(lines) <= max_lines and all(draw.textlength(ln, font=font) <= body_w for ln in lines):
            break
    y = top + bar + 48
    for line in lines:
        draw.text((left + 60, y), line, font=font, fill=PHOSPHOR)
        gd.text((left + 60, y), line, font=font, fill=PHOSPHOR_DIM)
        y += int(size * 1.18)
    if subtitle:
        small = _font(MONO_FONTS, 28, "ATLAS_OG_MONO_FONT")
        for line in _wrap(draw, subtitle, small, body_w, 2):
            if y + 40 > bottom - 24:
                break
            y += 14
            draw.text((left + 60, y), line, font=small, fill=INK_MUTED)
            y += 32

    if handle:
        prompt = f"$ {handle}"
        draw.text((left, 576), prompt, font=_font(MONO_FONTS, 26, "ATLAS_OG_MONO_FONT"), fill=INK, anchor="lm")
        x = left + draw.textlength(prompt, font=_font(MONO_FONTS, 26, "ATLAS_OG_MONO_FONT")) + 10
        draw.rectangle((x, 562, x + 14, 590), fill=PHOSPHOR)

    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(14)))
    # CRT scanlines: darken every third row.
    lines = Image.new("L", (WIDTH, HEIGHT), 0)
    ld = ImageDraw.Draw(lines)
    for row in range(0, HEIGHT, 3):
        ld.line((0, row, WIDTH, row), fill=70)
    return Image.composite(Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0)), img, lines)


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
