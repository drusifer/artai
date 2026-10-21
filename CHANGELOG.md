# Changelog

## Unreleased — Sprint 2 "Move recard and GlobalHeadsOrTails onto artai" (2026-10-20)

- recard and GlobalHeadsOrTails now make their art with artai, pip-installed editable from
  `../artai` by their own make targets; existing masters were reused (no quota spent).
- Their old tools (recard `tools/imagegen`, GlobalHeadsOrTails `tools/art_generator.py`), tests,
  docs and every reference to them are removed; artai's migration guide and source survey with them.
- ADR-0006: how consumers install artai.
- `generate` no longer repaints items that already have a packed image (e.g. a fresh clone without masters); `pack` skips up-to-date outputs. Both take `--force`; `generate --force` archives the old files to `rejected/` first.

## Unreleased — Sprint 1 "One art tool for every project" (2026-10-20)

Version bump to 0.2.0 awaits owner approval (docs/SDLC.md §6, Release class).

### Added
- `artai` CLI consolidating recard `tools/imagegen` and GlobalHeadsOrTails `tools/art_generator.py`
  (plus its deleted `sticker_art.mjs` / `nanobanana_backend.mjs` features).
- Manifests: GHOT YAML sets (inline items or `data_file` + `item_template`), recard TSV/JSON lists.
- Commands: `status`, `prompts`, `generate`, `pack`, `review`, `verify`, `regenerate`, `unlock`.
- Generation: resumable by image size, quota stops the run (exit 2), retries, timeouts,
  1–8 parallel workers, safe concurrent processes via per-item claims, Ctrl-C cleanup (exit 130).
- Providers: `codex` (sandboxed), `agy`, `gemini` (API), `command` (no shell), `mock` (tagged placeholders).
- Pack: `contain` and `autocrop` fitting; WebP/PNG/JPEG. Contact sheet HTML; `verify` gate.
- Docs: USAGE, MIGRATION, ARCH, DECISIONS (ADR-0001…0005), SDLC, LESSONS.
