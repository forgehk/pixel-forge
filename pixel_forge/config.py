"""Config parsing for the batch CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

@dataclass
class TargetSelector:
    hue: tuple[float, float]                  # (low, high) in 0..360, supports wrap
    saturation_min: float = 0.15

@dataclass
class Variant:
    name: str
    target_hue: float
    target_saturation: float | None = None
    target_value_shift: float = 0.0

@dataclass
class BatchConfig:
    input: Path
    output_dir: Path
    target: TargetSelector
    variants: list[Variant] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "BatchConfig":
        with path.open() as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data, base_dir=path.parent)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: Path = Path(".")) -> "BatchConfig":
        target = data.get("target", {}) or {}
        t = TargetSelector(
            hue=tuple(target.get("hue", [340, 360])),  # default: reds
            saturation_min=float(target.get("saturation_min", 0.15)),
        )
        variants = [
            Variant(
                name=v["name"],
                target_hue=float(v["target_hue"]),
                target_saturation=(
                    float(v["target_saturation"]) if "target_saturation" in v else None
                ),
                target_value_shift=float(v.get("target_value_shift", 0.0)),
            )
            for v in data.get("variants", []) or []
        ]
        return cls(
            input=(base_dir / data["input"]).resolve(),
            output_dir=(base_dir / data.get("output_dir", "out")).resolve(),
            target=t,
            variants=variants,
        )
