"""Tests for the YAML config loader."""

from pathlib import Path

from pixel_forge.config import BatchConfig

def test_from_dict_basic():
    data = {
        "input": "base.png",
        "output_dir": "out/",
        "target": {"hue": [340, 360], "saturation_min": 0.4},
        "variants": [
            {"name": "navy", "target_hue": 220, "target_saturation": 0.8},
            {"name": "forest", "target_hue": 140},
        ],
    }
    cfg = BatchConfig.from_dict(data, base_dir=Path("/tmp"))
    assert cfg.input.name == "base.png"
    assert cfg.target.hue == (340, 360)
    assert cfg.target.saturation_min == 0.4
    assert len(cfg.variants) == 2
    assert cfg.variants[0].name == "navy"
    assert cfg.variants[0].target_saturation == 0.8
    assert cfg.variants[1].target_saturation is None

def test_defaults():
    cfg = BatchConfig.from_dict(
        {"input": "x.png", "variants": []}, base_dir=Path("/tmp")
    )
    assert cfg.target.hue == (340, 360)
    assert cfg.target.saturation_min == 0.15
