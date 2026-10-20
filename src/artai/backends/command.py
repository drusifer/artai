"""Run a command line from the manifest (GlobalHeadsOrTails' ``cli`` backend), without a shell.

The template is split like a shell would split it, then placeholders are substituted inside
each argument, so a prompt containing quotes or ``;`` stays one argument and runs nothing.
"""

from __future__ import annotations

import shlex

from artai.backends._proc import is_quota, run_logged
from artai.backends.base import GenerationFailed, Job, QuotaExhausted
from artai.errors import ConfigError
from artai.model import ArtSet, Item


class CommandBackend:
    name = "command"

    def __init__(self, art_set: ArtSet):
        self.art_set = art_set
        self.template = art_set.command

    def preflight(self, items: list[Item], selected_count: int) -> None:
        if not self.template.strip():
            raise ConfigError(
                f"{self.art_set.source.name}: the command backend needs artwork_set.command "
                '(or cli_command) in a YAML manifest, e.g. command: "mytool --out {output} {prompt}"'
            )
        try:
            shlex.split(self.template)
        except ValueError as error:
            raise ConfigError(f"{self.art_set.source.name}: command cannot be parsed ({error})") from None

    def argv(self, job: Job) -> list[str]:
        values = {
            "{prompt}": job.prompt,
            "{id}": job.id,
            "{output}": str(job.master),
            "{output_path}": str(job.master),
            "{resolution}": f"{self.art_set.resolution[0]}x{self.art_set.resolution[1]}",
        }
        argv = []
        for token in shlex.split(self.template):
            for key, value in values.items():
                token = token.replace(key, value)
            argv.append(token)
        return argv

    def generate(self, job: Job) -> None:
        job.master.parent.mkdir(parents=True, exist_ok=True)
        code, output = run_logged(self.argv(job), job.log, job.timeout)
        if code == 0:
            return
        if is_quota(output):
            raise QuotaExhausted(output.strip().splitlines()[-1] if output.strip() else "quota")
        tail = output.strip().splitlines()[-1] if output.strip() else f"exit {code}"
        raise GenerationFailed(tail[:500])
