"""Backend registry: one entry per provider; an unknown name is an error, never a fallback."""

from __future__ import annotations

from collections.abc import Callable

from artai.backends.agy import AgyBackend
from artai.backends.base import Backend
from artai.backends.codex import CodexBackend
from artai.backends.command import CommandBackend
from artai.backends.gemini import GeminiBackend
from artai.backends.mock import MockBackend
from artai.errors import ConfigError
from artai.model import ArtSet

REGISTRY: dict[str, Callable[[ArtSet], Backend]] = {
    "agy": AgyBackend,
    "codex": CodexBackend,
    "command": CommandBackend,
    "gemini": GeminiBackend,
    "mock": MockBackend,
}


def backend_names() -> list[str]:
    return sorted(REGISTRY)


BACKEND_NAMES = backend_names()


def get_backend(name: str, art_set: ArtSet) -> Backend:
    factory = REGISTRY.get(name)
    if factory is None:
        raise ConfigError(f"unknown backend '{name}' (choose one of: {', '.join(backend_names())})")
    return factory(art_set)
