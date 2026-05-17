"""HSV-based recoloring.

The core trick: working in HSV instead of RGB lets us swap *which* color a
pixel is (hue) and *how saturated* it is (saturation) while preserving the
lighting (value). That preserves shadows, highlights, and texture, which is
exactly what you want for a product photo variant.
"""

from __future__ import annotations

import colorsys
from pathlib import Path

from PIL import Image

def recolor_pixels(
    pixels: list[tuple[int, int, int, int]],
    *,
    source_hue_range: tuple[float, float],
    target_hue: float,
    target_saturation: float | None = None,
    target_value_shift: float = 0.0,
    min_saturation_to_recolor: float = 0.15,
) -> list[tuple[int, int, int, int]]:
    """Recolor RGBA pixels in place.

    Args:
        pixels: list of (r, g, b, a) 0-255 tuples.
        source_hue_range: which hues (0-360) to recolor. Supports wrap-around
            (e.g. (340, 20) catches the red band straddling 0).
        target_hue: new hue in 0-360.
        target_saturation: if given, replace saturation with this (0-1).
            If None, saturation is preserved.
        target_value_shift: add this to the value channel (-1..+1), clamped.
        min_saturation_to_recolor: skip near-grey/white/black pixels.
            Threshold is 0-1.

    Returns:
        A new list of pixels with the same length and ordering.
    """
    lo, hi = source_hue_range
    lo /= 360.0
    hi /= 360.0
    new_hue = (target_hue % 360) / 360.0
    out: list[tuple[int, int, int, int]] = []

    for r, g, b, a in pixels:
        rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
        h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)
        if s < min_saturation_to_recolor:
            # near-grey: leave untouched.
            out.append((r, g, b, a))
            continue
        if _hue_in_range(h, lo, hi):
            h = new_hue
            if target_saturation is not None:
                s = max(0.0, min(1.0, target_saturation))
            if target_value_shift:
                v = max(0.0, min(1.0, v + target_value_shift))
            rf, gf, bf = colorsys.hsv_to_rgb(h, s, v)
            out.append((int(round(rf * 255)), int(round(gf * 255)), int(round(bf * 255)), a))
        else:
            out.append((r, g, b, a))
    return out

def _hue_in_range(h: float, lo: float, hi: float) -> bool:
    """Hue is in [lo, hi] on the 0..1 hue circle.

    Handles wrap-around two ways:
      - explicit wrap: lo > hi (e.g. lo=0.95, hi=0.05 — the red band at 0)
      - implicit wrap at the endpoint: a range ending at 1.0 also includes 0,
        because hue 0 and hue 1.0 are the same point on the color wheel.
    """
    EPS = 1e-9
    # Implicit wrap: pure red has hue=0, but humans write its range as (340, 360).
    if h <= EPS and hi >= 1.0 - EPS:
        return True
    if lo <= hi:
        return lo <= h <= hi
    # explicit wrap-around: e.g. lo=0.95, hi=0.05 (the red band around 0).
    return h >= lo or h <= hi

def recolor(
    image_path: str | Path,
    *,
    source_hue_range: tuple[float, float],
    target_hue: float,
    target_saturation: float | None = None,
    target_value_shift: float = 0.0,
    min_saturation_to_recolor: float = 0.15,
) -> Image.Image:
    """Recolor an image file. Returns the recolored Image."""
    img = Image.open(image_path).convert("RGBA")
    pixels = list(img.getdata())
    new_pixels = recolor_pixels(
        pixels,
        source_hue_range=source_hue_range,
        target_hue=target_hue,
        target_saturation=target_saturation,
        target_value_shift=target_value_shift,
        min_saturation_to_recolor=min_saturation_to_recolor,
    )
    out = Image.new("RGBA", img.size)
    out.putdata(new_pixels)
    return out
