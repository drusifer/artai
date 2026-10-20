# Changelog

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
