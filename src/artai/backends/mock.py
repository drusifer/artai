"""Offline placeholder art: deterministic per id, tagged so it never counts as real art."""

from __future__ import annotations

import hashlib

from PIL import Image, ImageDraw

from artai.backends._proc import append_log
from artai.backends.base import Job
from artai.imaging import save_png
from artai.model import ArtSet, Item

SIZE = 1024


class MockBackend:
    name = "mock"

    def __init__(self, art_set: ArtSet):
        self.art_set = art_set

    def preflight(self, items: list[Item], selected_count: int) -> None:
        return None

    def generate(self, job: Job) -> None:
        digest = int(hashlib.md5(job.id.encode("utf-8")).hexdigest(), 16)
        fill = (40 + digest % 180, 40 + (digest >> 8) % 180, 40 + (digest >> 16) % 180)
        image = Image.new("RGB", (SIZE, SIZE), (248, 246, 240))
        draw = ImageDraw.Draw(image)
        margin = int(SIZE * 0.15)
        draw.rounded_rectangle(
            [margin, margin, SIZE - margin, SIZE - margin],
            radius=24,
            fill=fill,
            outline=(20, 20, 20),
            width=4,
        )
        quarter = SIZE // 4
        draw.ellipse(
            [
                quarter + margin // 2,
                quarter + margin // 2,
                3 * quarter - margin // 2,
                3 * quarter - margin // 2,
            ],
            fill=tuple(min(255, c + 40) for c in fill),
        )
        draw.text((SIZE // 2 - len(job.id) * 3, SIZE // 2), job.id, fill=(255, 255, 255))
        save_png(image, job.master, placeholder="mock")
        append_log(job.log, "mock placeholder written")
