"""Tests for the HSV-based recoloring functions."""

from __future__ import annotations

import colorsys

from pixel_forge.recolor import recolor_pixels, _hue_in_range

def _hue_of(pixel: tuple[int, int, int, int]) -> float:
    r, g, b, _ = pixel
    h, _, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360

def test_red_pixel_becomes_blue():
    # pure red
    red = [(255, 0, 0, 255)]
    out = recolor_pixels(
        red,
        source_hue_range=(340, 360),
        target_hue=220,
        target_saturation=0.8,
    )
    h = _hue_of(out[0])
    # Should be near 220
    assert 215 <= h <= 225

def test_grey_pixel_unchanged():
    grey = [(128, 128, 128, 255)]
    out = recolor_pixels(
        grey,
        source_hue_range=(0, 360),
        target_hue=140,
        target_saturation=0.5,
        min_saturation_to_recolor=0.15,
    )
    assert out[0] == grey[0]

def test_out_of_range_pixel_unchanged():
    # green pixel, source hue is red — should not change
    green = [(0, 200, 0, 255)]
    out = recolor_pixels(
        green,
        source_hue_range=(340, 360),
        target_hue=220,
    )
    assert out[0] == green[0]

def test_wraparound_hue_range_catches_red():
    # The red band wraps around 0: e.g. (350, 10) should include hue 5.
    red = [(255, 40, 40, 255)]   # hue close to 0
    out = recolor_pixels(
        red,
        source_hue_range=(350, 10),
        target_hue=220,
        target_saturation=0.8,
    )
    h = _hue_of(out[0])
    assert 215 <= h <= 225

def test_alpha_preserved():
    p = [(200, 30, 30, 128)]
    out = recolor_pixels(p, source_hue_range=(340, 360), target_hue=120)
    assert out[0][3] == 128

def test_value_shift_darkens():
    p = [(200, 30, 30, 255)]
    out = recolor_pixels(
        p,
        source_hue_range=(340, 360),
        target_hue=220,
        target_value_shift=-0.3,
    )
    # darker than the original
    r0, g0, b0, _ = p[0]
    r1, g1, b1, _ = out[0]
    assert max(r1, g1, b1) < max(r0, g0, b0)

def test_hue_in_range_simple():
    assert _hue_in_range(0.5, 0.4, 0.6)
    assert not _hue_in_range(0.5, 0.6, 0.8)

def test_hue_in_range_wraparound():
    # range 0.95..0.05 should include 0.0
    assert _hue_in_range(0.0, 0.95, 0.05)
    assert _hue_in_range(0.97, 0.95, 0.05)
    assert not _hue_in_range(0.5, 0.95, 0.05)
