"""Turn masters into packed web assets (ADR-0002: masters are kept; packing is cheap and repeatable)."""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from artai.imaging import fit_autocrop, fit_contain, save_as
from artai.model import ArtSet, Item

FORMATS = ("webp", "png", "jpeg")


@dataclass
class PackSummary:
    packed: int = 0
    total: int = 0
    skipped: list[str] = field(default_factory=list)


def pack(art_set: ArtSet, items: list[Item]) -> PackSummary:
    """Pack every item that has a master. Unopenable masters are skipped and their old output kept."""
    summary = PackSummary()
    art_set.output_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        source = item.master(art_set)
        if not source.is_file():
            continue
        summary.total += 1
        try:
            with Image.open(source) as image:
                image.load()
                if art_set.fit == "autocrop":
                    fitted = fit_autocrop(image, art_set.resolution, art_set.pad)
                else:
                    fitted = fit_contain(image, art_set.size)
        except (OSError, ValueError):
            summary.skipped.append(item.id)
            continue
        save_as(fitted, item.packed(art_set), art_set.format, art_set.quality)
        summary.packed += 1
    return summary
