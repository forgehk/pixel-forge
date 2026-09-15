"""End-to-end tests for the CLI: YAML config on disk in, PNG files out."""

from __future__ import annotations

import colorsys

import pytest
import yaml
from PIL import Image

from pixel_forge.cli import main
from pixel_forge.config import BatchConfig
from pixel_forge.recolor import _flattened_data

RED = (220, 30, 30, 255)
GREY = (128, 128, 128, 255)

def _hue_of(pixel: tuple[int, int, int, int]) -> float:
    r, g, b, _ = pixel
    h, _, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360

def _write_base_image(path):
    """A 2x1 image: one saturated red pixel, one neutral grey pixel."""
    img = Image.new("RGBA", (2, 1))
    img.putdata([RED, GREY])
    img.save(path)

def _write_config(tmp_path, **overrides):
    _write_base_image(tmp_path / "base.png")
    data = {
        "input": "base.png",
        "output_dir": "out",
        "target": {"hue": [340, 360], "saturation_min": 0.4},
        "variants": [
            {"name": "navy", "target_hue": 220, "target_saturation": 0.8},
            {"name": "forest", "target_hue": 140, "target_saturation": 0.55},
        ],
    }
    data.update(overrides)
    config_path = tmp_path / "variants.yaml"
    config_path.write_text(yaml.safe_dump(data))
    return config_path

def test_from_yaml_resolves_paths_relative_to_the_config(tmp_path):
    config_path = _write_config(tmp_path)
    cfg = BatchConfig.from_yaml(config_path)
    assert cfg.input == tmp_path / "base.png"
    assert cfg.output_dir == tmp_path / "out"
    assert [v.name for v in cfg.variants] == ["navy", "forest"]

def test_build_writes_one_file_per_variant(tmp_path):
    config_path = _write_config(tmp_path)

    assert main(["build", str(config_path)]) == 0

    out = tmp_path / "out"
    assert sorted(p.name for p in out.iterdir()) == ["base-forest.png", "base-navy.png"]

def test_build_recolors_the_product_and_leaves_the_background_alone(tmp_path):
    config_path = _write_config(tmp_path)

    assert main(["build", str(config_path)]) == 0

    navy = _flattened_data(Image.open(tmp_path / "out" / "base-navy.png").convert("RGBA"))
    assert _hue_of(navy[0]) == pytest.approx(220, abs=5)
    assert navy[1] == GREY

def test_build_keeps_the_input_extension(tmp_path):
    _write_base_image(tmp_path / "base.webp")
    config_path = tmp_path / "variants.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "input": "base.webp",
                "output_dir": "out",
                "variants": [{"name": "navy", "target_hue": 220}],
            }
        )
    )

    assert main(["build", str(config_path)]) == 0
    assert (tmp_path / "out" / "base-navy.webp").exists()

def test_preview_writes_a_single_variant(tmp_path):
    config_path = _write_config(tmp_path)

    assert main(["preview", str(config_path), "--variant", "forest"]) == 0

    out = tmp_path / "out"
    assert [p.name for p in out.iterdir()] == ["preview-forest.png"]

def test_preview_of_an_unknown_variant_fails(tmp_path, capsys):
    config_path = _write_config(tmp_path)

    assert main(["preview", str(config_path), "--variant", "teal"]) == 1
    assert "teal" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()

def test_flattened_data_reads_pixels_on_any_pillow():
    img = Image.new("RGBA", (2, 1))
    img.putdata([(255, 0, 0, 255), (0, 0, 255, 128)])
    assert _flattened_data(img) == [(255, 0, 0, 255), (0, 0, 255, 128)]
