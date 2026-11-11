"""
Generate branded preview cards for portfolio projects with Pillow.

Cards mimic the site's dark theme with a cyan→blue accent. No system fonts are
required: we try a few common TrueType paths and otherwise fall back to Pillow's
built-in scalable default font (Pillow >= 10.1).
"""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 1200, 630

# Site palette
BG_TOP = (12, 18, 32)      # #0c1220
BG_BOTTOM = (5, 7, 13)     # #05070d
ACCENT_A = (34, 211, 238)  # cyan  #22d3ee
ACCENT_B = (59, 130, 246)  # blue  #3b82f6
TEXT = (237, 242, 247)
MUTED = (148, 163, 184)
CHIP_BG = (23, 32, 48)
CHIP_BORDER = (45, 64, 90)

_FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "DejaVuSans-Bold.ttf",
]
_FONT_CANDIDATES_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "DejaVuSans.ttf",
]


def _font(size: int, bold: bool = False):
    for path in (_FONT_CANDIDATES_BOLD if bold else _FONT_CANDIDATES_REG):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    # Pillow >= 10.1 returns a scalable DejaVu-based default when given a size.
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _vertical_gradient(w, h, top, bottom):
    base = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        draw.line([(0, y), (w, y)], fill=_lerp(top, bottom, y / max(1, h - 1)))
    return base


def _text_width(draw, text, font):
    return draw.textlength(text, font=font)


def _wrap(draw, text, font, max_width):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if _text_width(draw, trial, font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def generate_card(title: str, techs, repo_full: str) -> bytes:
    """Return PNG bytes for a project preview card.

    title: project title; techs: iterable of tech names; repo_full: e.g. 'A1isherDev/shop'.
    """
    img = _vertical_gradient(CARD_W, CARD_H, BG_TOP, BG_BOTTOM)

    # Soft accent glow in the top-right corner.
    glow = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([CARD_W - 520, -360, CARD_W + 220, 380], fill=(34, 211, 238, 38))
    gd.ellipse([CARD_W - 360, -260, CARD_W + 160, 280], fill=(59, 130, 246, 38))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    draw = ImageDraw.Draw(img)
    margin = 90

    # Left accent bar (cyan→blue).
    bar_x, bar_top, bar_bottom = margin, 150, CARD_H - 150
    for y in range(bar_top, bar_bottom):
        t = (y - bar_top) / max(1, bar_bottom - bar_top)
        draw.line([(bar_x, y), (bar_x + 10, y)], fill=_lerp(ACCENT_A, ACCENT_B, t))

    content_x = bar_x + 44
    content_w = CARD_W - content_x - margin

    # Eyebrow label.
    eyebrow = _font(30, bold=True)
    draw.text((content_x, 120), "PROJECT", font=eyebrow, fill=ACCENT_A)

    # Title (wrapped, max 3 lines).
    title_font = _font(76, bold=True)
    lines = _wrap(draw, title, title_font, content_w)[:3]
    y = 176
    for line in lines:
        draw.text((content_x, y), line, font=title_font, fill=TEXT)
        y += 90

    # Tech chips (up to 4).
    chip_font = _font(30, bold=False)
    chip_y = max(y + 26, 430)
    chip_x = content_x
    pad_x, chip_h, gap = 24, 56, 16
    for tech in list(techs)[:4]:
        tw = _text_width(draw, tech, chip_font)
        cw = tw + pad_x * 2
        if chip_x + cw > CARD_W - margin:
            break
        draw.rounded_rectangle(
            [chip_x, chip_y, chip_x + cw, chip_y + chip_h],
            radius=chip_h // 2, fill=CHIP_BG, outline=CHIP_BORDER, width=2,
        )
        draw.text((chip_x + pad_x, chip_y + (chip_h - 38) // 2), tech,
                  font=chip_font, fill=(203, 213, 225))
        chip_x += cw + gap

    # Footer: github path + identity.
    foot_font = _font(28, bold=False)
    draw.text((content_x, CARD_H - 96), f"github.com/{repo_full}",
              font=foot_font, fill=MUTED)
    name_font = _font(28, bold=True)
    name = "Alisher Muhammadaliyev"
    nx = CARD_W - margin - _text_width(draw, name, name_font)
    draw.text((nx, CARD_H - 96), name, font=name_font, fill=(203, 213, 225))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
