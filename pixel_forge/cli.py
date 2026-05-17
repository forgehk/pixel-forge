"""pixel-forge CLI."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .config import BatchConfig
from .recolor import recolor

def _build(config_path: Path) -> int:
    cfg = BatchConfig.from_yaml(config_path)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    base = cfg.input.stem
    ext = cfg.input.suffix or ".png"
    total = 0.0
    print(f"pixel-forge: {cfg.input.name} → {len(cfg.variants)} variants")
    for v in cfg.variants:
        t0 = time.perf_counter()
        img = recolor(
            cfg.input,
            source_hue_range=cfg.target.hue,
            target_hue=v.target_hue,
            target_saturation=v.target_saturation,
            target_value_shift=v.target_value_shift,
            min_saturation_to_recolor=cfg.target.saturation_min,
        )
        out_path = cfg.output_dir / f"{base}-{v.name}{ext}"
        img.save(out_path)
        dt = time.perf_counter() - t0
        total += dt
        print(f"  ✓ {v.name:<12}  hue={v.target_hue:<5}  {dt*1000:.0f}ms  → {out_path.name}")
    print(f"\nDone in {total*1000:.0f}ms total.")
    return 0

def _preview(config_path: Path, variant_name: str, show: bool) -> int:
    cfg = BatchConfig.from_yaml(config_path)
    variant = next((v for v in cfg.variants if v.name == variant_name), None)
    if variant is None:
        print(f"No variant named {variant_name!r} in config.", file=sys.stderr)
        return 1
    img = recolor(
        cfg.input,
        source_hue_range=cfg.target.hue,
        target_hue=variant.target_hue,
        target_saturation=variant.target_saturation,
        target_value_shift=variant.target_value_shift,
        min_saturation_to_recolor=cfg.target.saturation_min,
    )
    if show:
        img.show()
    else:
        out_path = cfg.output_dir / f"preview-{variant.name}.png"
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        print(f"wrote {out_path}")
    return 0

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pixel-forge",
        description="HSV-based product color variants.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="Build all variants from a YAML config.")
    b.add_argument("config", type=Path, help="Path to YAML config.")

    p = sub.add_parser("preview", help="Render a single variant.")
    p.add_argument("config", type=Path)
    p.add_argument("--variant", required=True, help="Variant name.")
    p.add_argument("--show", action="store_true", help="Open in default viewer instead of saving.")

    args = parser.parse_args(argv)
    if args.command == "build":
        return _build(args.config.resolve())
    if args.command == "preview":
        return _preview(args.config.resolve(), args.variant, args.show)
    return 1

if __name__ == "__main__":
    sys.exit(main())
