"""Contact sheet for human review, and ``verify`` — the check that means "this set is done"."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from PIL import Image

from artai.imaging import is_placeholder, write_bytes_atomic
from artai.model import ArtSet, Item
from artai.prompts import render

# ── verify ─────────────────────────────────────────────────────────────────


@dataclass
class VerifyReport:
    checked: int = 0
    problems: list[tuple[str, str]] = field(default_factory=list)
    duplicates: list[tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems and not self.duplicates


def _size_problem(art_set: ArtSet, size: tuple[int, int]) -> str | None:
    width, height = size
    if art_set.fit == "autocrop":
        if size != art_set.resolution:
            return f"is {width}x{height}, expected {art_set.resolution[0]}x{art_set.resolution[1]}"
    elif max(size) != art_set.size:
        return f"is {width}x{height}, expected longest edge {art_set.size}"
    return None


def verify(art_set: ArtSet, items: list[Item], allow_mock: bool = False) -> VerifyReport:
    report = VerifyReport(checked=len(items))
    seen: dict[str, str] = {}
    for item in items:
        packed = item.packed(art_set)
        if not packed.is_file():
            hint = " (master exists — run artai pack)" if item.master(art_set).is_file() else ""
            report.problems.append((item.id, "no packed image" + hint))
            continue
        try:
            with Image.open(packed) as image:
                image.load()
                size = image.size
        except (OSError, ValueError):
            report.problems.append((item.id, "packed image does not open"))
            continue
        problem = _size_problem(art_set, size)
        if problem:
            report.problems.append((item.id, problem))
        if not allow_mock and is_placeholder(item.master(art_set)):
            report.problems.append((item.id, "placeholder art (mock)"))
        digest = hashlib.sha256(packed.read_bytes()).hexdigest()
        if digest in seen:
            report.duplicates.append((seen[digest], item.id))
        else:
            seen[digest] = item.id
    return report


# ── contact sheet ──────────────────────────────────────────────────────────

STYLE = """
:root { --bg:#f6f7f9; --card:#fff; --text:#16181d; --muted:#5d6470; --line:#e2e5ea; --accent:#2563eb;
        --ok-bg:#dcfce7; --ok:#166534; --warn-bg:#fef3c7; --warn:#92400e; --bad-bg:#fee2e2; --bad:#991b1b; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#111317; --card:#1a1d23; --text:#e8eaed; --muted:#9aa3ae; --line:#2b3038; --accent:#7aa2ff;
          --ok-bg:#12351f; --ok:#86efac; --warn-bg:#3b2c0b; --warn:#fcd34d; --bad-bg:#3d1515; --bad:#fca5a5; }
}
* { box-sizing: border-box; }
body { margin:0; padding:16px; background:var(--bg); color:var(--text);
       font:15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width:1440px; margin:0 auto; }
header { background:var(--card); border:1px solid var(--line); border-radius:12px;
         padding:16px 20px; margin-bottom:16px; }
h1 { margin:0 0 4px; font-size:1.5rem; }
.desc { margin:0 0 12px; color:var(--muted); }
.stats { display:flex; flex-wrap:wrap; gap:8px; font-size:.85rem; }
.stats span { border:1px solid var(--line); border-radius:8px; padding:4px 10px;
              overflow-wrap:anywhere; min-width:0; }
input[type=search] { width:100%; margin:0 0 16px; padding:10px 14px; font-size:1rem; color:var(--text);
                     background:var(--card); border:1px solid var(--line); border-radius:8px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(min(240px, 100%), 1fr)); gap:16px; }
.art-card { background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden;
            display:flex; flex-direction:column; }
.thumb { aspect-ratio:1; display:flex; align-items:center; justify-content:center; background:var(--bg); }
.thumb img { width:100%; height:100%; object-fit:contain; display:block; }
.thumb .missing { color:var(--bad); font-weight:600; }
.info { padding:12px; display:flex; flex-direction:column; gap:6px; flex:1; }
.row { display:flex; justify-content:space-between; gap:8px; align-items:center; }
.id { font-weight:700; font-size:.9rem; overflow-wrap:anywhere; }
.title { color:var(--muted); font-size:.85rem; }
.pill { font-size:.72rem; font-weight:700; padding:2px 8px; border-radius:12px; white-space:nowrap; }
.ready { background:var(--ok-bg); color:var(--ok); }
.placeholder { background:var(--warn-bg); color:var(--warn); }
.absent { background:var(--bad-bg); color:var(--bad); }
.tags { display:flex; flex-wrap:wrap; gap:4px; }
.tags span { font-size:.72rem; border:1px solid var(--line); border-radius:4px;
             padding:1px 6px; color:var(--muted); }
details { margin-top:auto; font-size:.78rem; border-top:1px dashed var(--line); padding-top:6px; }
summary { cursor:pointer; color:var(--accent); font-weight:600; }
details p { margin:6px 0 0; white-space:pre-wrap; overflow-wrap:anywhere; }
details dt { font-weight:700; margin-top:6px; }
details dd { margin:0; overflow-wrap:anywhere; }
"""

SHORT = 40  # metadata values longer than this are shown under "details", not as tags

SCRIPT = """
const box = document.getElementById('filter');
box.addEventListener('input', () => {
  const q = box.value.toLowerCase();
  document.querySelectorAll('.art-card').forEach(card => {
    card.hidden = !card.textContent.toLowerCase().includes(q);
  });
});
"""


def _card(art_set: ArtSet, item: Item, page_dir: Path) -> tuple[str, bool]:
    packed = item.packed(art_set)
    ready = packed.is_file()
    if ready:
        link = escape(Path(os.path.relpath(packed, page_dir)).as_posix())
        thumb = (
            f'<a href="{link}" target="_blank"><img loading="lazy" src="{link}" alt="{escape(item.id)}"></a>'
        )
        if is_placeholder(item.master(art_set)):
            pill = '<span class="pill placeholder">Placeholder</span>'
        else:
            pill = f'<span class="pill ready">Ready · {packed.stat().st_size / 1024:.0f} KB</span>'
    else:
        thumb = '<span class="missing">Missing</span>'
        pill = '<span class="pill absent">Missing</span>'
    title = escape(str(item.metadata.get("name") or ""))
    fields = [
        (str(k), str(v))
        for k, v in item.metadata.items()
        if k not in ("name", "id", "prompt", "prompt_template")
        and isinstance(v, (str, int, float))
        and str(v)
    ]
    # Short values are tags; long ones (lore, descriptions) go in the expandable details.
    tags = "".join(f"<span><b>{escape(k)}</b>: {escape(v)}</span>" for k, v in fields if len(v) <= SHORT)
    long_fields = "".join(f"<dt>{escape(k)}</dt><dd>{escape(v)}</dd>" for k, v in fields if len(v) > SHORT)
    card = (
        f'<article class="art-card"><div class="thumb">{thumb}</div><div class="info">'
        f'<div class="row"><span class="id">{escape(item.id)}</span>{pill}</div>'
        + (f'<div class="title">{title}</div>' if title else "")
        + (f'<div class="tags">{tags}</div>' if tags else "")
        + f"<details><summary>Prompt &amp; details</summary><p>{escape(render(art_set, item).prompt)}</p>"
        + (f"<dl>{long_fields}</dl>" if long_fields else "")
        + "</details>"
        "</div></article>"
    )
    return card, ready


def build_contact_sheet(art_set: ArtSet, items: list[Item]) -> Path:
    page_dir = art_set.review_dir
    page_dir.mkdir(parents=True, exist_ok=True)
    cards, ready = [], 0
    for item in items:
        card, is_ready = _card(art_set, item, page_dir)
        cards.append(card)
        ready += is_ready
    description = f'<p class="desc">{escape(art_set.description)}</p>' if art_set.description else ""
    geometry = (
        f"{art_set.resolution[0]}×{art_set.resolution[1]} autocrop"
        if art_set.fit == "autocrop"
        else f"longest edge {art_set.size}"
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(art_set.name)} contact sheet</title><style>{STYLE}</style></head>
<body><main>
<header><h1>{escape(art_set.name)}</h1>{description}
<div class="stats"><span>Packed: <b>{ready} of {len(items)}</b></span>
<span>{geometry} · {escape(art_set.format)}</span>
<span>{escape(str(art_set.output_dir))}</span></div></header>
<input type="search" id="filter" aria-label="Filter artwork"
       placeholder="Filter by id, name or any metadata…">
<section class="grid">{"".join(cards)}</section>
</main><script>{SCRIPT}</script></body></html>
"""
    page = page_dir / "contact_sheet.html"
    write_bytes_atomic(page, html.encode("utf-8"))
    return page
