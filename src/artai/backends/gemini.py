"""Gemini image API ("Nano Banana") over HTTPS, using only the standard library.

The key comes from GEMINI_API_KEY and is sent only in a request header — never logged.
"""

from __future__ import annotations

import base64
import json
import math
import mimetypes
import os
import re
import urllib.error
import urllib.request

from artai.backends._proc import append_log, is_quota
from artai.backends._prompt import checked_reference, reference_clause
from artai.backends.base import GenerationFailed, Job, QuotaExhausted
from artai.errors import ConfigError
from artai.imaging import write_bytes_atomic
from artai.model import ArtSet, Item

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-nano-banana-2.1"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
REFERENCE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def aspect_ratio(width: int, height: int) -> str:
    divisor = math.gcd(width, height) or 1
    ratio = f"{width // divisor}:{height // divisor}"
    return ratio if ratio in RATIOS else "1:1"


class GeminiBackend:
    name = "gemini"

    def __init__(self, art_set: ArtSet):
        self.art_set = art_set
        self.key = os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("ARTAI_GEMINI_MODEL", DEFAULT_MODEL)
        self.endpoint = os.environ.get("ARTAI_GEMINI_ENDPOINT", ENDPOINT)

    def preflight(self, items: list[Item], selected_count: int) -> None:
        if not self.key:
            raise ConfigError("the gemini backend needs GEMINI_API_KEY set in the environment")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.model):
            raise ConfigError(f"ARTAI_GEMINI_MODEL contains unsupported characters: {self.model!r}")

    def _scrub(self, text: str) -> str:
        return text.replace(self.key, "***") if self.key else text

    def body(self, job: Job) -> dict:
        reference = checked_reference(job)
        prompt = job.prompt + (reference_clause("attached") if reference else "")
        parts: list[dict] = [{"type": "text", "text": prompt}]
        if reference is not None:
            mime = REFERENCE_TYPES.get(reference.suffix.lower()) or mimetypes.guess_type(reference.name)[0]
            if not mime:
                raise GenerationFailed(f"unsupported reference image type: {reference.name}")
            parts.append(
                {
                    "type": "image",
                    "mime_type": mime,
                    "data": base64.b64encode(reference.read_bytes()).decode(),
                }
            )
        width, height = self.art_set.resolution
        return {
            "model": self.model,
            "input": parts,
            "response_format": {
                "type": "image",
                "mime_type": "image/png",
                "aspect_ratio": aspect_ratio(width, height),
                "image_size": "1K",
            },
        }

    def generate(self, job: Job) -> None:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(self.body(job)).encode(),
            headers={"content-type": "application/json", "x-goog-api-key": self.key},
            method="POST",
        )
        append_log(job.log, f"gemini: POST model {self.model}")
        try:
            with urllib.request.urlopen(request, timeout=job.timeout) as response:
                status, text = response.status, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            message = self._scrub(f"gemini request failed: {getattr(error, 'reason', error)}")
            append_log(job.log, message)
            raise GenerationFailed(message) from None

        try:
            result = json.loads(text)
        except ValueError:
            result = {}
        if not isinstance(result, dict):
            result = {}
        if status != 200:
            error = result.get("error")
            message = error.get("message") if isinstance(error, dict) else None
            detail = self._scrub(str(message or text))[:500]
            append_log(job.log, f"gemini: HTTP {status}: {detail}")
            if status == 429 or is_quota(detail):
                raise QuotaExhausted(f"gemini HTTP {status}: {detail}")
            raise GenerationFailed(f"gemini HTTP {status}: {detail}")

        encoded = (result.get("output_image") or {}).get("data")
        if not isinstance(encoded, str) or not encoded:
            detail = self._scrub(
                str(result.get("output_text") or result.get("status") or "no image in response")
            )
            append_log(job.log, f"gemini: no image: {detail[:500]}")
            raise GenerationFailed(f"gemini produced no image: {detail[:500]}")
        image = base64.b64decode(encoded, validate=False)
        if not image.startswith(PNG_SIGNATURE):
            append_log(job.log, "gemini: response was not a PNG")
            raise GenerationFailed("gemini response was not a PNG image")
        write_bytes_atomic(job.master, image)
        append_log(job.log, f"gemini: wrote {len(image)} bytes")
