"""In-process stand-in backends for runner tests."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from PIL import Image

from artai.backends.base import GenerationFailed, Job, QuotaExhausted
from artai.imaging import save_png


def paint(path: Path, size: int = 600) -> None:
    save_png(Image.new("RGB", (size, size), (10, 120, 200)), path)


class Scripted:
    """Backend whose behaviour per call comes from a script: 'ok', 'fail', 'quota', 'tiny', 'none'."""

    name = "scripted"

    def __init__(self, script: dict[str, list[str]] | None = None, default: str = "ok", delay: float = 0.0):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.default = default
        self.delay = delay
        self.calls: list[str] = []
        self.lock = threading.Lock()

    def preflight(self, items, selected_count) -> None:
        pass

    def generate(self, job: Job) -> None:
        with self.lock:
            self.calls.append(job.id)
            steps = self.script.get(job.id)
            action = steps.pop(0) if steps else self.default
        time.sleep(self.delay)
        if action == "ok":
            paint(job.master)
        elif action == "tiny":
            paint(job.master, size=100)
        elif action == "fail":
            raise GenerationFailed("provider said no")
        elif action == "quota":
            raise QuotaExhausted("You've hit your usage limit")
        elif action == "none":
            return
        else:
            raise AssertionError(action)
