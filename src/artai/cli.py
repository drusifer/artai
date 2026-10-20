"""artai command line: ``artai <command> <manifest> [options]``.

Exit codes: 0 success, 1 error or failed items, 2 provider quota exhausted.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable

from artai import __version__
from artai.errors import ArtaiError
from artai.manifest import load_manifest
from artai.model import FITS, ArtSet, Item
from artai.prompts import render

MISSING_SHOWN = 8


def _load(args: argparse.Namespace) -> tuple[ArtSet, list[Item]]:
    return load_manifest(args.manifest, work=args.work, out=args.out, style=args.style, fit=args.fit)


# ── commands ───────────────────────────────────────────────────────────────


def cmd_prompts(args: argparse.Namespace) -> int:
    art_set, items = _load(args)
    rows = []
    for item in items:
        rendered = render(art_set, item)
        for key in rendered.missing:
            print(f"warning: {item.id}: no value for placeholder {{{key}}}", file=sys.stderr)
        rows.append((item, rendered.prompt))
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": i.id,
                        "filename": i.packed_name(art_set.format),
                        "prompt": p,
                        "metadata": i.metadata,
                    }
                    for i, p in rows
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for item, prompt in rows:
            print(f"{item.id}\t{prompt}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    art_set, items = _load(args)
    masters = [i for i in items if i.master(art_set).is_file()]
    missing = [i for i in items if not i.packed(art_set).is_file()]
    print(f"set:          {art_set.name}")
    print(f"manifest:     {art_set.source}")
    print(f"items:        {len(items)}")
    print(f"masters:      {len(masters)}   ({art_set.masters_dir})")
    print(f"packed:       {len(items) - len(missing)}   ({art_set.output_dir})")
    print(f"missing:      {len(missing)}")
    for item in missing[:MISSING_SHOWN]:
        print(f"  {item.id}")
    if len(missing) > MISSING_SHOWN:
        print(f"  ... and {len(missing) - MISSING_SHOWN} more")
    if art_set.quota_marker.is_file():
        stamp = art_set.quota_marker.read_text(encoding="utf-8").strip()
        print(f"quota:        exhausted at {stamp} — re-run generate after the provider resets")
    return 0


# ── parser ─────────────────────────────────────────────────────────────────

Command = Callable[[argparse.Namespace], int]


def _common() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("manifest", help="YAML set, TSV (<id><TAB><prompt>) or JSON list of {id, prompt}")
    common.add_argument("--work", metavar="DIR", help="work directory: masters, logs, claims")
    common.add_argument("--out", metavar="DIR", help="directory for packed images (overrides manifest)")
    common.add_argument("--style", metavar="TEXT", help="style text appended to every prompt")
    common.add_argument("--fit", choices=FITS, help="how pack frames images (overrides manifest)")
    return common


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="artai", description="Manifest-driven AI artwork generation.")
    parser.add_argument("-V", "--version", action="version", version=f"artai {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    common = _common()

    p = sub.add_parser("status", parents=[common], help="count masters, packed and missing images")
    p.set_defaults(handler=cmd_status)

    p = sub.add_parser("prompts", parents=[common], help="print every item's final prompt")
    p.add_argument("--json", action="store_true", help="print JSON (id, filename, prompt, metadata)")
    p.set_defaults(handler=cmd_prompts)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as exit_:
        return int(exit_.code or 0)
    if not getattr(args, "handler", None):
        parser.print_usage(sys.stderr)
        return 1
    try:
        return args.handler(args)
    except ArtaiError as error:
        print(f"artai: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
