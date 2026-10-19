# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""Render the README banner as dark and light SVGs.

Text is converted to outlines so the banner looks the same without the fonts installed.
Run from the repo root: uv run scripts/banner.py
"""

import math
import random
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

NAME = "Jeremy Moebel"
SUBTITLE = "computer vision · generative models · ML engineering"

FONTS = {
    "serif": "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf",
    "mono": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
}
FONT_CACHE = Path.home() / ".cache" / "profile-banner-fonts"

WIDTH, HEIGHT = 880, 200

THEMES = {
    "dark": {"bg": "#0d1117", "fg": "#e6edf3", "muted": "#8b949e", "border": "#30363d",
             "from": (68, 147, 248), "to": (163, 113, 247)},
    "light": {"bg": "#ffffff", "fg": "#1f2328", "muted": "#59636e", "border": "#d1d9e0",
              "from": (9, 105, 218), "to": (130, 80, 223)},
}


def font(key: str) -> TTFont:
    path = FONT_CACHE / Path(FONTS[key]).name
    if not path.exists():
        FONT_CACHE.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FONTS[key], path)
    return TTFont(path)


def text_path(tt: TTFont, text: str, x: float, baseline: float, size: float, tracking: float = 0) -> str:
    """SVG path data for `text`, with its baseline at (x, baseline)."""
    glyph_set = tt.getGlyphSet()
    cmap = tt.getBestCmap()
    scale = size / tt["head"].unitsPerEm
    pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    cursor = x
    for char in text:
        name = cmap[ord(char)]
        glyph_set[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline)))
        cursor += glyph_set[name].width * scale + tracking
    return pen.getCommands()


def pixel_field(theme: dict) -> list[str]:
    """Grid of squares that goes from noise on the left to a smooth pattern on the right."""
    rng = random.Random(7)
    cols, rows, cell, gap, x0, y0 = 28, 14, 9, 3, 532, 16
    rects = []
    for c in range(cols):
        t = c / (cols - 1)
        for r in range(rows):
            clean = 0.15 + 0.85 * (1 - abs(r - rows / 2) / (rows / 2)) * (0.55 + 0.45 * math.sin(c / 4 + r / 6))
            noise = rng.random() * (1 if rng.random() < 0.55 else 0)
            alpha = min(1, max(0, (1 - t) * noise + t * clean))
            if alpha < 0.06:
                continue
            mix = r / (rows - 1)
            rgb = ",".join(str(round(a + (b - a) * mix)) for a, b in zip(theme["from"], theme["to"]))
            rects.append(
                f'<rect x="{x0 + c * (cell + gap)}" y="{y0 + r * (cell + gap)}" width="{cell}" height="{cell}" '
                f'rx="1.5" fill="rgb({rgb})" fill-opacity="{alpha * 0.85:.2f}"/>'
            )
    return rects


def render(theme: dict) -> str:
    serif, mono = font("serif"), font("mono")
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{NAME}">',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="6" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        *pixel_field(theme),
        '<defs><linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{theme["bg"]}"/><stop offset="1" stop-color="{theme["bg"]}" stop-opacity="0"/>'
        "</linearGradient></defs>",
        f'<rect x="520" y="1" width="90" height="{HEIGHT - 2}" fill="url(#fade)"/>',
        f'<path fill="{theme["fg"]}" d="{text_path(serif, NAME, 40, 110, 64)}"/>',
        f'<path fill="{theme["muted"]}" d="{text_path(mono, SUBTITLE, 42, 146, 13, tracking=0.5)}"/>',
        "</svg>",
    ])


if __name__ == "__main__":
    out = Path("assets")
    out.mkdir(exist_ok=True)
    for mode, theme in THEMES.items():
        (out / f"banner-{mode}.svg").write_text(render(theme) + "\n")
        print(f"wrote {out / f'banner-{mode}.svg'}")
