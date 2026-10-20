"""Google Antigravity CLI (``agy``).

agy may save into its own scratch directory whatever path it is given, so after it exits the
newest ``<id>.png`` / ``<id>_N.png`` there is moved into place. Its permission bypass is only
allowed for a single, explicitly opted-in item: headless agy otherwise soft-denies tools.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from artai.backends._proc import is_quota, run_logged
from artai.backends._prompt import agent_prompt
from artai.backends.base import GenerationFailed, Job, QuotaExhausted
from artai.errors import ConfigError
from artai.model import ArtSet, Item

DEFAULT_SCRATCH = Path.home() / ".gemini/antigravity-cli/scratch"


class AgyBackend:
    name = "agy"

    def __init__(self, art_set: ArtSet):
        self.art_set = art_set
        self.cli = os.environ.get("ARTAI_AGY_CLI", "agy")
        self.scratch = Path(os.environ.get("ARTAI_AGY_SCRATCH", DEFAULT_SCRATCH)).expanduser()
        self.model = os.environ.get("ARTAI_AGY_MODEL", "")
        self.yolo = os.environ.get("ARTAI_AGY_YOLO") == "1"

    def preflight(self, items: list[Item], selected_count: int) -> None:
        if self.yolo and selected_count != 1:
            raise ConfigError(
                f"ARTAI_AGY_YOLO=1 bypasses agy's permission checks and is only allowed for exactly one "
                f"item (select it with --ids); {selected_count} selected"
            )

    def argv(self, job: Job) -> list[str]:
        prompt = agent_prompt(
            job,
            f"Call the built-in generate_image tool, name the file {job.id}.png and save the PNG exactly to "
            f"{job.master}. Do not create SVG or code-drawn art. If image generation is unavailable, "
            "return an error and do not substitute another method.",
        )
        minutes = max(1, round(job.timeout / 60))
        argv = [
            self.cli,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--print-timeout",
            f"{minutes}m",
            "--sandbox",
        ]
        if self.model:
            argv += ["--model", self.model]
        if self.yolo:
            argv.append("--dangerously-skip-permissions")
        return argv

    def claim_from_scratch(self, job: Job) -> bool:
        try:
            candidates = [
                p
                for p in self.scratch.iterdir()
                if p.name == f"{job.id}.png" or p.name.startswith(f"{job.id}_")
            ]
        except OSError:
            return False
        if not candidates:
            return False
        newest = max(candidates, key=lambda p: p.stat().st_mtime)
        shutil.move(str(newest), job.master)
        return True

    def generate(self, job: Job) -> None:
        job.master.parent.mkdir(parents=True, exist_ok=True)
        code, output = run_logged(self.argv(job), job.log, job.timeout, cwd=job.master.parent)
        if job.master.is_file() or self.claim_from_scratch(job):
            return
        if is_quota(output):
            raise QuotaExhausted("agy reported a usage/quota limit")
        raise GenerationFailed(f"agy exited {code} without producing {job.id}.png")
