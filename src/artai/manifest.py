"""Load any manifest kind (YAML set, TSV list, JSON list) into an ArtSet and its Items.

The YAML schema is a superset of GlobalHeadsOrTails' ``art_generator.py``; TSV/JSON lists are
recard's ``imagegen`` job lists. Every problem raises ManifestError naming the file, before
anything is written.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from artai.errors import ManifestError
from artai.model import FITS, SAFE_ID, ArtSet, Item

YAML_SUFFIXES = {".yaml", ".yml"}
TSV_SUFFIXES = {".tsv", ".txt"}


def load_manifest(
    path: Path | str,
    *,
    work: str | Path | None = None,
    out: str | Path | None = None,
    style: str | None = None,
    fit: str | None = None,
) -> tuple[ArtSet, list[Item]]:
    """Load ``path``; keyword arguments are command-line overrides (None = not given)."""
    path = Path(path)
    if not path.is_file():
        raise ManifestError(f"{path}: manifest not found")
    suffix = path.suffix.lower()
    if suffix in YAML_SUFFIXES:
        art_set, items = _load_yaml(path)
    elif suffix in TSV_SUFFIXES:
        art_set, items = _list_set(path), _parse_tsv(path)
    elif suffix == ".json":
        art_set, items = _list_set(path), _parse_json_list(path)
    else:
        raise ManifestError(f"{path.name}: unsupported manifest type '{suffix}' (use .yaml, .tsv or .json)")

    _check_ids(path, items)
    return _apply_overrides(art_set, work=work, out=out, style=style, fit=fit), items


# ── overrides and paths ────────────────────────────────────────────────────


def _resolve(value: str | Path) -> Path:
    """Relative paths resolve against the directory artai runs from."""
    return (Path.cwd() / Path(value)).resolve()


def _apply_overrides(
    art_set: ArtSet,
    *,
    work: str | Path | None,
    out: str | Path | None,
    style: str | None,
    fit: str | None,
) -> ArtSet:
    changes: dict[str, Any] = {}
    if work is not None:
        changes["work_dir"] = _resolve(work)
        if art_set.review_dir == art_set.work_dir / "review":
            changes["review_dir"] = changes["work_dir"] / "review"
        if art_set.kind == "list" and out is None:
            changes["output_dir"] = changes["work_dir"] / "out"
    if out is not None:
        changes["output_dir"] = _resolve(out)
    if style is not None:
        changes["style"] = style
    if fit is not None:
        changes["fit"] = _check_fit(art_set.source, fit)
    return replace(art_set, **changes) if changes else art_set


def _check_fit(path: Path, fit: str) -> str:
    if fit not in FITS:
        raise ManifestError(f"{path.name}: fit must be one of {', '.join(FITS)}, got '{fit}'")
    return fit


def _check_ids(path: Path, items: list[Item]) -> None:
    seen: set[str] = set()
    for item in items:
        if not SAFE_ID.fullmatch(item.id):
            raise ManifestError(
                f'{path.name}: unsafe id "{item.id}" — ids become filenames, so they may only '
                "contain letters, digits, dot, dash and underscore"
            )
        if item.id in seen:
            raise ManifestError(f'{path.name}: duplicate id "{item.id}" — it would overwrite the first')
        seen.add(item.id)


# ── recard-style lists ─────────────────────────────────────────────────────


def _list_set(path: Path) -> ArtSet:
    work_dir = _resolve(Path("build/artai") / path.stem)
    return ArtSet(
        name=path.stem,
        kind="list",
        source=path.resolve(),
        work_dir=work_dir,
        output_dir=work_dir / "out",
        review_dir=work_dir / "review",
        fit="contain",
        quality=88,
    )


def _parse_tsv(path: Path) -> list[Item]:
    items = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        # Split on the first tab only: a prompt may itself contain tabs.
        item_id, tab, prompt = line.partition("\t")
        if not tab or not item_id.strip() or not prompt.strip():
            raise ManifestError(f'{path.name}: line {number}: expected <id><TAB><prompt>, got "{line[:40]}"')
        items.append(Item(id=item_id.strip(), prompt=prompt.strip()))
    return items


def _parse_json_list(path: Path) -> list[Item]:
    data = _read_json(path)
    if not isinstance(data, list):
        raise ManifestError(f"{path.name}: expected a JSON list of {{id, prompt}} entries")
    items = []
    for number, entry in enumerate(data, 1):
        if not isinstance(entry, dict) or not str(entry.get("id", "")).strip():
            raise ManifestError(f"{path.name}: entry {number}: missing id")
        if not str(entry.get("prompt", "")).strip():
            raise ManifestError(f"{path.name}: entry {number}: missing prompt")
        items.append(Item(id=str(entry["id"]).strip(), prompt=str(entry["prompt"]).strip()))
    return items


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"{path.name}: not valid JSON ({error})") from None


# ── YAML sets ──────────────────────────────────────────────────────────────


def _parse_resolution(path: Path, value: Any) -> tuple[int, int]:
    try:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return int(value[0]), int(value[1])
        if isinstance(value, int):
            return value, value
        if isinstance(value, str):
            width, _, height = value.lower().replace(" ", "").partition("x")
            return int(width), int(height)
    except ValueError:
        pass
    raise ManifestError(f"{path.name}: resolution must look like [512, 512] or '512x512', got {value!r}")


def _load_yaml(path: Path) -> tuple[ArtSet, list[Item]]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ManifestError(f"{path.name}: not valid YAML ({error})") from None
    if not isinstance(raw, dict):
        raise ManifestError(f"{path.name}: expected a mapping with an 'artwork_set' section")
    meta = raw.get("artwork_set") or {}
    if not isinstance(meta, dict):
        raise ManifestError(f"{path.name}: 'artwork_set' must be a mapping")
    return _yaml_set(path, meta), _yaml_items(path, raw)


def _yaml_set(path: Path, meta: dict[str, Any]) -> ArtSet:
    name = str(meta.get("name") or path.stem).strip()
    work_dir = _resolve(meta.get("work_dir") or Path("build/artai") / name)
    output_dir = _resolve(meta["output_dir"]) if meta.get("output_dir") else work_dir / "out"
    review_dir = _resolve(meta["review_dir"]) if meta.get("review_dir") else work_dir / "review"
    if "fit" in meta:
        fit = _check_fit(path, str(meta["fit"]))
    else:
        fit = "autocrop" if meta.get("autocrop", True) else "contain"
    try:
        numbers = {
            key: int(meta.get(key, default))
            for key, default in (("size", 512), ("pad", 10), ("quality", 92), ("min_size", 512))
        }
    except (TypeError, ValueError) as error:
        message = f"{path.name}: size, pad, quality and min_size must be whole numbers ({error})"
        raise ManifestError(message) from None
    return ArtSet(
        name=name,
        kind="yaml",
        source=path.resolve(),
        work_dir=work_dir,
        output_dir=output_dir,
        review_dir=review_dir,
        description=str(meta.get("description", "")),
        theme=str(meta.get("theme", "")).strip(),
        style=str(meta.get("style", "")).strip(),
        default_template=str(meta.get("default_template", "{prompt}")),
        fit=fit,
        resolution=_parse_resolution(path, meta.get("resolution", (512, 512))),
        format=str(meta.get("format", "webp")).lower(),
        command=str(meta.get("command") or meta.get("cli_command") or ""),
        **numbers,
    )


def _yaml_items(path: Path, raw: dict[str, Any]) -> list[Item]:
    entries = raw.get("items")
    if entries is None:
        entries = _data_file_entries(path, raw)
    if not isinstance(entries, list):
        raise ManifestError(f"{path.name}: 'items' must be a list")
    items = []
    for number, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            raise ManifestError(f"{path.name}: item {number}: expected a mapping")
        item_id = str(entry.get("id", "")).strip()
        if not item_id:
            raise ManifestError(f"{path.name}: item {number}: missing id")
        metadata = entry.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {"value": str(metadata)}
        reference = str(entry.get("reference_image", "") or "").strip()
        items.append(
            Item(
                id=item_id,
                prompt=str(entry.get("prompt", "")).strip(),
                prompt_template=str(entry.get("prompt_template", "") or "").strip(),
                metadata=metadata,
                output_filename=str(entry.get("output_filename", "") or "").strip(),
                reference_image=(path.parent / reference).resolve() if reference else None,
            )
        )
    return items


def _data_file_entries(path: Path, raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand ``data_file`` records with ``item_template`` into item entries (GHOT semantics)."""
    data_name = str(raw.get("data_file", "cards.json"))
    data_path = (path.parent / data_name).resolve()
    if not data_path.is_file():
        raise ManifestError(f"{path.name}: data_file '{data_name}' not found at {data_path}")
    data = _read_json(data_path)
    if isinstance(data, dict):
        data = data.get("items") or data.get("cards")
    if not isinstance(data, list):
        raise ManifestError(f'{data_path.name}: expected a JSON list of records (or {{"items": [...]}})')

    template_cfg = raw.get("item_template", {})
    if isinstance(template_cfg, dict):
        default_template = str(template_cfg.get("prompt_template", "") or "")
    else:
        default_template = str(template_cfg or "")

    entries = []
    for record in data:
        if not isinstance(record, dict):
            continue
        entries.append(
            {
                "id": record.get("id", ""),
                "prompt": record.get("prompt", ""),
                "prompt_template": record.get("prompt_template") or default_template,
                "metadata": record,
                "output_filename": record.get("output_filename", ""),
                "reference_image": record.get("reference_image", ""),
            }
        )
    return entries
