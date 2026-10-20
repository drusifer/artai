"""All Pillow work: validation, placeholder tags and atomic writes (fitting is added by pack)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PIL import Image, PngImagePlugin

PLACEHOLDER_KEY = "artai-placeholder"


def is_valid(path: Path, min_size: int) -> bool:
    """True when ``path`` opens as an image whose shorter edge is at least ``min_size``.

    Judged by dimensions, never bytes: good art can compress to a few KB.
    """
    try:
        with Image.open(path) as image:
            image.load()
            return min(image.size) >= min_size
    except (OSError, ValueError, Image.DecompressionBombError):
        return False


def is_placeholder(path: Path) -> bool:
    """True for masters drawn by the mock backend (tagged in a PNG text chunk)."""
    try:
        with Image.open(path) as image:
            return PLACEHOLDER_KEY in getattr(image, "text", {})
    except (OSError, ValueError):
        return False


def _temp_beside(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(handle)
    return Path(name)


def save_png(image: Image.Image, path: Path, placeholder: str | None = None) -> Path:
    """Write ``image`` as PNG atomically; tag it as placeholder art when ``placeholder`` is given."""
    info = PngImagePlugin.PngInfo()
    if placeholder:
        info.add_text(PLACEHOLDER_KEY, placeholder)
    temp = _temp_beside(path)
    try:
        image.save(temp, "PNG", pnginfo=info)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return path


def write_bytes_atomic(path: Path, data: bytes) -> Path:
    temp = _temp_beside(path)
    try:
        temp.write_bytes(data)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return path
