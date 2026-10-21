"""Turn masters into packed web assets (ADR-0002: masters are kept; packing is cheap and repeatable)."""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from artai.imaging import fit_autocrop, fit_contain, save_as
from artai.model import ArtSet, Item
from artai.review import size_problem

FORMATS = ("webp", "png", "jpeg")


@dataclass
class PackSummary:
    packed: int = 0
    current: int = 0  # outputs already up to date, left untouched
    total: int = 0
    skipped: list[str] = field(default_factory=list)


def _up_to_date(art_set: ArtSet, item: Item) -> bool:
    """The packed file exists, is newer than its master and has the size the set requires."""
    packed, master = item.packed(art_set), item.master(art_set)
    if not packed.is_file() or packed.stat().st_mtime < master.stat().st_mtime:
        return False
    try:
        with Image.open(packed) as image:
            return size_problem(art_set, image.size) is None
    except (OSError, ValueError):
        return False


def pack(art_set: ArtSet, items: list[Item], force: bool = False) -> PackSummary:
    """Pack every item that has a master and no up-to-date output (all of them with ``force``).
    Unopenable masters are skipped and their old output kept. A changed quality setting is not
    detectable from the file, so use ``force`` after changing it."""
    summary = PackSummary()
    art_set.output_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        source = item.master(art_set)
        if not source.is_file():
            continue
        summary.total += 1
        if not force and _up_to_date(art_set, item):
            summary.current += 1
            continue
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
