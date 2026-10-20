"""artai command line: ``artai <command> <manifest> [options]``.

Exit codes: 0 success, 1 error or failed items, 2 provider quota exhausted.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime

from artai import __version__
from artai.backends import backend_names, get_backend
from artai.claims import clear_stale, holder
from artai.errors import ArtaiError, ConfigError
from artai.imaging import is_placeholder, is_valid
from artai.manifest import load_manifest
from artai.model import FITS, ArtSet, Item
from artai.pack import FORMATS, pack
from artai.prompts import render
from artai.review import build_contact_sheet, verify
from artai.runner import RunOptions, RunSummary, run

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
    masters = [i for i in items if is_valid(i.master(art_set), 1)]
    placeholders = [i for i in masters if is_placeholder(i.master(art_set))]
    missing = [i for i in items if not i.packed(art_set).is_file()]
    print(f"set:          {art_set.name}")
    print(f"manifest:     {art_set.source}")
    print(f"items:        {len(items)}")
    print(f"masters:      {len(masters) - len(placeholders)}   ({art_set.masters_dir})")
    print(f"placeholders: {len(placeholders)}   (mock art — replaced by any real backend)")
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


def select(items: list[Item], ids: str | None) -> list[Item]:
    """Restrict to ``--ids a,b,c`` (manifest order); an unknown id is refused before anything runs."""
    if not ids:
        return items
    wanted = [part.strip() for part in ids.split(",") if part.strip()]
    known = {item.id for item in items}
    unknown = [i for i in wanted if i not in known]
    if unknown:
        raise ConfigError(f"unknown id {', '.join(unknown)} (not in the manifest)")
    chosen = set(wanted)
    return [item for item in items if item.id in chosen]


def _run_options(args: argparse.Namespace, art_set: ArtSet) -> RunOptions:
    def number(flag: str, raw: str, kind, low, high=None):
        try:
            value = kind(raw)
        except ValueError:
            value = None
        if value is None or value < low or (high is not None and value > high):
            span = f"{low}–{high}" if high is not None else f"at least {low}"
            raise ConfigError(f"{flag} must be a number {span}, got '{raw}'")
        return value

    return RunOptions(
        parallel=number("--parallel", args.parallel, int, 1, 8),
        retries=number("--retries", args.retries, int, 0),
        timeout=number("--timeout", args.timeout, float, 1),
        min_size=art_set.min_size if args.min_size is None else number("--min-size", args.min_size, int, 1),
        reverse=args.reverse,
    )


RESULT_LABEL = {"ok": "ok   ", "skip": "skip ", "busy": "busy ", "fail": "FAIL ", "quota": "QUOTA"}


def generate_items(args: argparse.Namespace, art_set: ArtSet, items: list[Item]) -> int:
    """Shared by generate and regenerate: validate options, preflight, run, report."""
    if not args.backend:
        raise ConfigError(f"--backend is required (choose one of: {', '.join(backend_names())})")
    options = _run_options(args, art_set)
    backend = get_backend(args.backend, art_set)
    backend.preflight(items, len(items))
    if art_set.quota_marker.is_file():
        stamp = art_set.quota_marker.read_text(encoding="utf-8").strip()
        print(f"note: the last run hit the provider quota at {stamp}; trying again")
    print(f"artai — {len(items)} item(s), backend {backend.name}, {options.parallel} at a time")
    print(f"masters → {art_set.masters_dir}")

    def progress(result: str, item: Item, done: int, total: int) -> None:
        print(f"{RESULT_LABEL[result]} [{done}/{total}] {item.id}", flush=True)

    started = time.monotonic()
    summary = run(art_set, items, backend, options, on_result=progress)
    return _report(summary, (time.monotonic() - started) / 60)


def _report(summary: RunSummary, minutes: float) -> int:
    print(
        f"\nartai — {summary.ok} generated, {summary.skipped} already present, "
        f"{len(summary.busy)} busy elsewhere, {len(summary.failed)} failed in {minutes:.1f} min",
        flush=True,
    )
    if summary.busy:
        print(f"busy (claimed by another live run): {', '.join(summary.busy)}")
    if summary.failed:
        print(f"failed: {', '.join(summary.failed)} — see the logs/ folder in the work directory", flush=True)
    if summary.quota:
        print(
            f"\n✖ provider quota exhausted — run stopped early ({summary.not_started} item(s) not started).\n"
            "  Re-run the same command after the quota resets; finished images are skipped.",
            file=sys.stderr,
        )
        return 2
    return 1 if summary.failed else 0


def cmd_generate(args: argparse.Namespace) -> int:
    art_set, items = _load(args)
    return generate_items(args, art_set, select(items, args.ids))


def cmd_pack(args: argparse.Namespace) -> int:
    from dataclasses import replace

    art_set, items = _load(args)
    changes: dict = {}
    if args.format:
        changes["format"] = args.format
    for flag, key, low, high in (("--quality", "quality", 1, 100), ("--size", "size", 1, 20000)):
        raw = getattr(args, key)
        if raw is not None:
            try:
                value = int(raw)
            except ValueError:
                value = 0
            if not low <= value <= high:
                raise ConfigError(f"{flag} must be a whole number {low}–{high}, got '{raw}'")
            changes[key] = value
    art_set = replace(art_set, **changes) if changes else art_set
    summary = pack(art_set, items)
    print(f"artai — packed {summary.packed}/{summary.total} → {art_set.output_dir}")
    if summary.skipped:
        print(f"skipped (master does not open): {', '.join(summary.skipped)}")
        return 1
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    art_set, items = _load(args)
    print(f"contact sheet: {build_contact_sheet(art_set, items)}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    art_set, all_items = _load(args)
    items = select(all_items, args.ids)
    report = verify(art_set, items, allow_mock=args.allow_mock)
    for item_id, problem in report.problems:
        print(f"✖ {item_id}: {problem}")
    for first, second in report.duplicates:
        print(f"✖ {first} and {second}: identical images")
    bad = len({i for i, _ in report.problems} | {i for pair in report.duplicates for i in pair})
    print(f"\nartai — {report.checked - bad}/{report.checked} verified for set {art_set.name}")
    if args.ids:
        print("note: this result covers the selected sample only and cannot show the set is complete")
    return 0 if report.ok else 1


def _require_ids(args: argparse.Namespace, items: list[Item], command: str) -> list[Item]:
    if not args.ids:
        raise ConfigError(f"{command} needs --ids (which items to {command}); it never acts on a whole set")
    return select(items, args.ids)


def _refuse_live(art_set: ArtSet, items: list[Item]) -> None:
    """All-or-nothing: refuse before touching anything if any selected item is being generated."""
    live = []
    for item in items:
        record, alive = holder(art_set.claims_dir, item.id)
        if alive:
            live.append(f"{item.id} is held by live process {record.get('pid')} on {record.get('host')}")
    if live:
        raise ConfigError("refused, nothing changed: " + "; ".join(live))


def cmd_regenerate(args: argparse.Namespace) -> int:
    art_set, all_items = _load(args)
    items = _require_ids(args, all_items, "regenerate")
    _refuse_live(art_set, items)
    if not args.backend:  # check before moving anything
        raise ConfigError(f"--backend is required (choose one of: {', '.join(backend_names())})")
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    archive = art_set.work_dir / "rejected" / stamp
    moved = 0
    for item in items:
        for source in (item.master(art_set), item.packed(art_set)):
            if source.is_file():
                archive.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), archive / source.name)
                moved += 1
    print(f"set aside {moved} file(s) → {archive}")
    code = generate_items(args, art_set, items)
    print(f"next: artai pack {args.manifest}   (the regenerated items have no packed image yet)")
    return code


def cmd_unlock(args: argparse.Namespace) -> int:
    art_set, all_items = _load(args)
    items = _require_ids(args, all_items, "unlock")
    _refuse_live(art_set, items)
    for item in items:
        had_claim = holder(art_set.claims_dir, item.id)[0] is not None
        clear_stale(art_set.claims_dir, item.id)
        print(f"cleared stale claim: {item.id}" if had_claim else f"no claim: {item.id}")
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


def _generation() -> argparse.ArgumentParser:
    gen = argparse.ArgumentParser(add_help=False)
    gen.add_argument("--backend", help="image provider (required): " + ", ".join(backend_names()))
    gen.add_argument("--parallel", default="2", metavar="N", help="items generated at once, 1–8 (default 2)")
    gen.add_argument("--retries", default="2", metavar="N", help="extra attempts after a failure (default 2)")
    gen.add_argument("--timeout", default="600", metavar="SEC", help="limit per provider call (default 600)")
    gen.add_argument(
        "--min-size", metavar="PX", help="smallest acceptable edge (default: manifest min_size, 512)"
    )
    gen.add_argument("--ids", metavar="A,B", help="only these item ids")
    gen.add_argument("--reverse", action="store_true", help="work from the end of the list")
    return gen


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

    p = sub.add_parser("generate", parents=[common, _generation()], help="paint missing masters (resumable)")
    p.set_defaults(handler=cmd_generate)

    p = sub.add_parser("pack", parents=[common], help="turn masters into packed web images")
    p.add_argument("--format", choices=FORMATS, help="output format (overrides manifest)")
    p.add_argument("--quality", metavar="Q", help="1–100 (overrides manifest)")
    p.add_argument("--size", metavar="PX", help="longest edge for --fit contain (overrides manifest)")
    p.set_defaults(handler=cmd_pack)

    p = sub.add_parser("review", parents=[common], help="write an HTML contact sheet")
    p.set_defaults(handler=cmd_review)

    p = sub.add_parser("verify", parents=[common], help="check every image exists, fits and is unique")
    p.add_argument("--ids", metavar="A,B", help="check only these ids (a sample, not proof of completeness)")
    p.add_argument("--allow-mock", action="store_true", help="accept mock placeholder art (for tests)")
    p.set_defaults(handler=cmd_verify)

    p = sub.add_parser(
        "regenerate",
        parents=[common, _generation()],
        help="set aside rejected images (--ids) and paint new ones",
    )
    p.set_defaults(handler=cmd_regenerate)

    p = sub.add_parser("unlock", parents=[common], help="clear claims left by a crashed run (--ids)")
    p.add_argument("--ids", metavar="A,B", help="items whose stale claims to clear")
    p.set_defaults(handler=cmd_unlock)
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
    except KeyboardInterrupt:
        print("\nartai: interrupted — finished images are kept; re-run to continue", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
