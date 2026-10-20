"""Prompt wording shared by the agent-CLI providers (codex, agy)."""

from __future__ import annotations

from artai.backends.base import GenerationFailed, Job

# Asked plainly for "an image", a coding agent sometimes writes a script that *draws* one.
# That happened in a real recard run, so the requirement is stated explicitly.
PREAMBLE = (
    "Generate a PNG image using your image generation tool — actual painted raster artwork. "
    "Do not write code to draw it."
)


def checked_reference(job: Job):
    """The job's reference image, failing the item if it names a file that does not exist."""
    if job.reference_image is not None and not job.reference_image.is_file():
        raise GenerationFailed(f"reference image not found: {job.reference_image}")
    return job.reference_image


def reference_clause(where: str) -> str:
    return (
        f" A reference image is {where}. Use it only as a likeness reference for identity and "
        "distinguishing features; create a fresh image in the requested style and do not copy "
        "lettering, text or watermarks from it."
    )


def agent_prompt(job: Job, save_instruction: str) -> str:
    reference = checked_reference(job)
    text = f"{PREAMBLE} Subject: {job.prompt}"
    if reference is not None:
        text += reference_clause(f"available at {reference}; open it and look at it before generating")
    return f"{text} {save_instruction}"
