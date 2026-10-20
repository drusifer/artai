# Art Tooling Survey — consolidation input (2026-10-20)

Sprint goal (User): consolidate the artwork generation tooling from `../recard` and
`../GlobalHeadsOrTails` (user wrote "GlobalHeadsAndTails"; the repo is `GlobalHeadsOrTails`)
into one new tool in `artai`.

## Source 1 — recard `tools/imagegen/` (Node ESM, ~510 lines, live)
- CLI: `imagegen gen --manifest jobs.tsv|json --out DIR [--backend codex|agy] [--style] [--parallel N] [--retries N] [--min-size N]`
  and `imagegen pack --in DIR --out DIR [--size N] [--quality N] [--format webp|png|jpeg]`.
- Manifest: TSV `<id>\t<prompt>` or JSON `[{id,prompt}]`; safe-id regex `^[\w.-]+$`, duplicate check.
- Backends registry: `codex` (`codex exec ... --dangerously-bypass-approvals-and-sandbox`, writes to path),
  `agy` (Antigravity; writes to shared scratch dir → runner "claims" the file). Shared prompt preamble
  ("use your image generation tool, do not write code to draw it"), shared QUOTA regex.
- Runner: resumable (skip existing valid image), quota is terminal (first quota error stops all lanes,
  writes `.quota-exhausted`, exit 2), bounded concurrency, retries, validate by DIMENSIONS not bytes.
- Pack: aspect-preserving thumbnail → WebP (Pillow via `python3 -c`).
- Tests: `recard/tests/imagegen.test.js`. Consumer: `make art-gen` / `make art` (RTG card art).

## Source 2 — GlobalHeadsOrTails `tools/art_generator.py` (Python, 892 lines, live)
- CLI: `--manifest m.yaml --status | --generate [--backend mock|cli] [--force] [--item ID] | --review | --export-prompts`.
- YAML manifest: `artwork_set` (name, output_dir, review_dir, theme, style, default_template, format,
  resolution, quality, autocrop, pad, cli_command) + inline `items` OR `data_file` + `item_template`
  (has a hardcoded `families/forms` special case — domain leak).
- Prompt engine: `{key}` interpolation from item metadata + set theme/style, unknown keys preserved.
- ImageProcessor: corner-sample autocrop, center, pad, fixed canvas, WebP q92.
- Backends: `MockBackend` (deterministic, offline tests) and `CLICommandBackend` (shell=True template).
- ContactSheetBuilder: searchable HTML review page.
- Tests: `tools/tests/test_art_generator.py` (335 lines). Manifests: 3 under
  `game_server/src/game_server/sticker_catalog/*/manifest.yaml`. Make: `art-status/art-generate/art-review`.
- **Regression vs. what it replaced**: no resumable validation, no quota handling, no parallelism,
  no retries, no real codex/agy/nanobanana backends, no locks, no reference images.

## Source 3 — GlobalHeadsOrTails deleted tools (recover from `git show b6e4e7e^:<path>`)
- `tools/sticker_art.mjs` (276): adapter over recard imagegen. Adds: `codex-safe` (no bypass flags,
  `--sandbox workspace-write`), per-image `.lock` files (multi-runner safe), 10-min timeout, per-image
  logs, reverse order, `ART_IDS` selection, verify (dimensions + duplicate-bitmap sha256), JPEG
  contact sheets (36/page), regenerate (archives rejected masters), unlock (checks live processes),
  reference-image prompt injection.
- `tools/nanobanana_backend.mjs` (56): direct Gemini API image backend (`GEMINI_API_KEY`,
  `NANOBANANA_MODEL`, reference image input, PNG signature check, atomic write).
- `tools/sticker_production.py` (140): detached production "lanes", quota report/clear-quota.
- `tools/sticker_references.py` (89): domain-specific (NHL portraits) — probably out of scope.
- `tools/STICKER_ART.md`: operating notes; lessons (agy soft-denies tools in headless; YOLO limited to 1 item).
- Production evidence: `build/rangers-art/` — 1162-item run, 478 done before quota block.

## Consolidation implications
- Best-of: GHOT YAML manifest + templates + autocrop + mock + HTML review, PLUS recard/sticker_art
  runner semantics (resume, quota-terminal, parallel, retries, locks, timeouts) and real backends
  (codex-safe, agy, nanobanana/Gemini API), plus pack/verify/regenerate.
- Domain-specific bits (Rangers catalog, NHL references, pack activation) stay in the consumer repos.
- Existing consumers: recard `make art-gen/art`, GHOT `make art-*` + 3 YAML manifests.
