"""The contract every image provider implements."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from artai.model import Item


class GenerationFailed(Exception):
    """This attempt produced no usable image; the runner may retry."""


class QuotaExhausted(Exception):
    """The provider is out of budget; the whole run must stop."""


@dataclass(frozen=True)
class Job:
    id: str
    prompt: str
    master: Path
    log: Path
    timeout: float
    reference_image: Path | None = None
    resolution: tuple[int, int] = (1024, 1024)


class Backend(Protocol):
    name: str

    def preflight(self, items: list[Item], selected_count: int) -> None:
        """Raise ConfigError before any item starts if this backend cannot run."""

    def generate(self, job: Job) -> None:
        """Write ``job.master`` or raise GenerationFailed / QuotaExhausted."""
