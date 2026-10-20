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


# ── fitting (used by pack) ─────────────────────────────────────────────────


def fit_contain(image: Image.Image, size: int) -> Image.Image:
    """Longest edge = ``size`` (never upscaled), aspect ratio preserved (recard ``pack``)."""
    fitted = image.convert("RGB")
    fitted.thumbnail((size, size), Image.Resampling.LANCZOS)
    return fitted


def fit_autocrop(image: Image.Image, resolution: tuple[int, int], pad: int) -> Image.Image:
    """Trim the plain background, centre the subject on an exact canvas (GlobalHeadsOrTails)."""
    from PIL import ImageChops

    rgb = image.convert("RGB")
    width, height = resolution
    background = rgb.getpixel((0, 0))
    difference = ImageChops.difference(rgb, Image.new("RGB", rgb.size, background))
    box = difference.point(lambda p: 255 if p > 16 else 0).getbbox()
    if not box:
        return rgb.resize((width, height), Image.Resampling.LANCZOS)
    subject = rgb.crop(box)
    scale = min(max(1, width - 2 * pad) / subject.width, max(1, height - 2 * pad) / subject.height)
    new_size = (max(1, int(subject.width * scale)), max(1, int(subject.height * scale)))
    canvas = Image.new("RGB", (width, height), background)
    canvas.paste(
        subject.resize(new_size, Image.Resampling.LANCZOS),
        ((width - new_size[0]) // 2, (height - new_size[1]) // 2),
    )
    return canvas


def save_as(image: Image.Image, path: Path, fmt: str, quality: int) -> Path:
    """Write ``image`` in ``fmt`` (webp/png/jpeg) atomically."""
    temp = _temp_beside(path)
    try:
        if fmt == "webp":
            image.save(temp, "WEBP", quality=quality, method=6)
        elif fmt in ("jpeg", "jpg"):
            image.convert("RGB").save(temp, "JPEG", quality=quality)
        else:
            image.save(temp, fmt.upper())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return path
