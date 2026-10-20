"""Render an item's final prompt.

Ported from GlobalHeadsOrTails' ``PromptEngine`` so existing manifests produce identical text:
``{key}`` tokens come from the item's metadata, then ``id``, ``prompt``, ``theme``, ``style``
and ``set_name``. Unknown tokens are left as written and reported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from artai.model import ArtSet, Item

TOKEN = re.compile(r"\{([a-zA-Z0-9_\-]+)\}")


@dataclass(frozen=True)
class Rendered:
    prompt: str
    missing: list[str] = field(default_factory=list)


def render(art_set: ArtSet, item: Item) -> Rendered:
    if item.prompt_template:
        template = item.prompt_template
    elif "{prompt}" in art_set.default_template:
        template = art_set.default_template
    elif item.prompt:
        template = item.prompt
    else:
        template = art_set.default_template

    context: dict[str, Any] = {
        "id": item.id,
        "prompt": item.prompt,
        "theme": art_set.theme,
        "style": art_set.style,
        "set_name": art_set.name,
    }
    context.update(item.metadata)
    missing: list[str] = []

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if context.get(key) is not None:
            return str(context[key])
        if key.lower() in context:
            return str(context[key.lower()])
        missing.append(key)
        return match.group(0)

    resolved = TOKEN.sub(substitute, template)

    # A bare prompt gets the set's theme and style appended (unless already present).
    if template in (item.prompt, "{prompt}"):
        parts = [resolved.strip()]
        for extra in (art_set.theme, art_set.style):
            if extra and extra not in resolved:
                parts.append(extra.strip())
        resolved = " ".join(part for part in parts if part)

    return Rendered(prompt=" ".join(resolved.split()), missing=missing)
