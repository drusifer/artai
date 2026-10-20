"""The two values everything else works on: an art set and its items."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Fit = Literal["autocrop", "contain"]
FITS: tuple[str, ...] = ("autocrop", "contain")

# An id becomes a filename, so it may not contain path separators or shell-hostile characters.
SAFE_ID = re.compile(r"[A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class ArtSet:
    name: str
    kind: Literal["yaml", "list"]
    source: Path
    work_dir: Path
    output_dir: Path
    review_dir: Path
    description: str = ""
    theme: str = ""
    style: str = ""
    default_template: str = "{prompt}"
    fit: Fit = "autocrop"
    resolution: tuple[int, int] = (512, 512)
    size: int = 512
    pad: int = 10
    format: str = "webp"
    quality: int = 92
    min_size: int = 512
    command: str = ""

    @property
    def masters_dir(self) -> Path:
        return self.work_dir / "masters"

    @property
    def logs_dir(self) -> Path:
        return self.work_dir / "logs"

    @property
    def claims_dir(self) -> Path:
        return self.work_dir / "claims"

    @property
    def quota_marker(self) -> Path:
        return self.work_dir / ".quota-exhausted"


@dataclass(frozen=True)
class Item:
    id: str
    prompt: str = ""
    prompt_template: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    output_filename: str = ""
    reference_image: Path | None = None

    def packed_name(self, fmt: str) -> str:
        return self.output_filename or f"{self.id}.{fmt}"

    def master(self, art_set: ArtSet) -> Path:
        return art_set.masters_dir / f"{self.id}.png"

    def packed(self, art_set: ArtSet) -> Path:
        return art_set.output_dir / self.packed_name(art_set.format)
