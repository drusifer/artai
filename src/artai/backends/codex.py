"""OpenAI Codex CLI. Runs in workspace-write sandbox; never with approval/sandbox bypass flags."""

from __future__ import annotations

import os

from artai.backends._proc import is_quota, run_logged
from artai.backends._prompt import agent_prompt
from artai.backends.base import GenerationFailed, Job, QuotaExhausted
from artai.model import ArtSet, Item


class CodexBackend:
    name = "codex"

    def __init__(self, art_set: ArtSet):
        self.art_set = art_set
        self.cli = os.environ.get("ARTAI_CODEX_CLI", "codex")

    def preflight(self, items: list[Item], selected_count: int) -> None:
        return None

    def argv(self, job: Job) -> list[str]:
        prompt = agent_prompt(job, f"Save it to {job.master}.")
        return [self.cli, "exec", "--sandbox", "workspace-write", "--skip-git-repo-check", prompt]

    def generate(self, job: Job) -> None:
        job.master.parent.mkdir(parents=True, exist_ok=True)
        # cwd = masters dir: the sandbox lets codex write inside its workspace.
        code, output = run_logged(self.argv(job), job.log, job.timeout, cwd=job.master.parent)
        if job.master.is_file():
            return
        if is_quota(output):
            raise QuotaExhausted("codex reported a usage/quota limit")
        raise GenerationFailed(f"codex exited {code} without writing {job.master.name}")
