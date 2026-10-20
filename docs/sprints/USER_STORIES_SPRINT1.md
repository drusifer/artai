# Sprint 1 User Stories: One art tool for every project

> Note (Sprint 2): `docs/MIGRATION.md` and `agents/oracle/art_tooling_survey.md`, referenced below, were deleted once the migration landed; see git history.

*   **Total Points**: 24 (Tier 1)
*   **Branch**: `main` (per `docs/SDLC.md` §6 — no sprint branches; one commit per approved phase)
*   **Source**: User, 2026-10-20, `$sprint consolidate the art work generation tooling from ../recard and ../GlobalHeadsAndTails into a new tool in this repo` (agents/CHAT.md). Decisions on 2026-10-20: Python; build the tool only (no consumer migration); commit per phase on main.
*   **Status**: Done — all 7 stories accepted (docs/sprints/UAT_PLAN_SPRINT1.md). Architecture: docs/ARCH.md

## Goal

Today three diverging art pipelines exist: recard's `tools/imagegen` (resumable, quota-aware,
real backends), GlobalHeadsOrTails' `tools/art_generator.py` (YAML manifests, prompt templates,
autocrop, HTML review — but only a mock and a raw shell backend), and GlobalHeadsOrTails'
deleted `sticker_art.mjs` / `nanobanana_backend.mjs` (locks, safe codex, Gemini API, verify,
regenerate). When this sprint is done, an operator producing art for any project uses one
`artai` command that does all of it, and both existing projects' art sets can be run through it
unchanged. Source survey: `agents/oracle/art_tooling_survey.md`.

## Assumptions made for the owner

1. The command is called `artai`, run from this checkout (`make run ARGS=...` or `.venv/bin/artai`). If wrong: only the entry-point name changes.
2. The GlobalHeadsOrTails YAML manifest is the primary format, and recard's TSV/JSON id+prompt lists are also accepted, so neither project has to rewrite its inputs. If wrong: STORY-ART-1 AC 2 is dropped.
3. The `codex` backend runs **without** recard's `--dangerously-bypass-approvals-and-sandbox` flag, following GlobalHeadsOrTails' later "codex-safe" decision. If wrong: an explicit opt-in flag can be added later.
4. Real providers (codex, agy, Gemini) are verified in tests with stand-in programs and a stubbed HTTP endpoint, not by spending quota. A live sample run is the owner's call (Open Question 1).
5. Project-specific tooling stays in its project: the Rangers catalog builder, NHL portrait reference fetching, sticker-pack activation and the sticker gallery server are not consolidated. If wrong: they become backlog stories.
6. Long-running detached "production lanes" (`sticker_production.py`) are replaced by running several `artai generate` processes at once, which the per-item locking in STORY-ART-2 makes safe. If wrong: lane management becomes a backlog story.

---

## STORY-ART-1: Describe an art set once and preview it
**Points:** 3

**As an** operator preparing artwork for a project,
**I want** to describe the whole set (style, theme, sizes, items and prompt templates) in one manifest and see what will be generated before spending any quota,
**so that** I catch bad prompts and missing items while they are free to fix.

### Acceptance Criteria
1. Given a YAML manifest with an `artwork_set` section and inline `items`, `artai prompts <manifest>` prints every item's id and its final prompt, with `{name}`-style placeholders filled from the item's metadata and the set's `theme`/`style`.
2. A manifest that is a recard-style TSV (`<id><TAB><prompt>` per line, `#` comments allowed) or JSON list of `{id, prompt}` is accepted by every command, with the style taken from `--style` on the command line.
3. A YAML manifest may instead name a `data_file` (JSON list of records) plus an `item_template`; each record becomes an item and all its fields are usable as placeholders.
4. `artai status <manifest>` prints the set name, the total item count, how many finished images exist, how many are missing, and up to 8 missing ids (followed by "... and N more" when there are more).
5. A manifest with a duplicate id, an id containing anything other than letters, digits, `.`, `-`, `_`, a missing `data_file`, or an unreadable YAML/TSV line is rejected with a message naming the file and the offending id or line number, exit code 1, and nothing is written.
6. A placeholder that no item field or set value supplies (e.g. `{jersey}`) is reported by `artai prompts` as a warning naming the item and placeholder; the prompt is still printed with the placeholder left as written.
7. Every command accepts `--work <dir>` (masters, logs, claims) and `--out <dir>` (packed images), overriding the manifest. Without them: YAML sets use the manifest's `work_dir` (default `build/artai/<set name>`) and `output_dir` (default `build/artai/<set name>/out`); TSV/JSON lists use `build/artai/<file name without extension>` and its `out/` folder. Relative paths resolve against the directory `artai` is run from.

## STORY-ART-2: Generate a whole set without ever paying twice
**Points:** 5

**As an** operator running a long, quota-limited generation job,
**I want** `artai generate` to pick up exactly where it stopped, stop cleanly when quota runs out, and run safely in several terminals at once,
**so that** interruptions, quota lockouts and parallel runs never waste generations or corrupt output.

### Acceptance Criteria
1. `artai generate <manifest> --backend mock` produces one original ("master") image per item in the set's work directory, entirely offline.
2. Re-running the same command generates nothing for items whose master already exists and opens at ≥ the minimum size (default 512 px on the shorter edge); the summary line reports them as "already present". A file that is too small or does not open is regenerated, regardless of its byte size.
3. When a backend reports a quota/rate-limit error, no further items are started, a quota marker file is left in the work directory, the summary says the quota was exhausted and that re-running after reset resumes, and the exit code is 2.
4. An ordinary failure is retried up to `--retries` times (default 2); items still failing are listed by id in the summary and the exit code is 1. A single backend call that runs longer than `--timeout` (default 10 minutes) counts as a failure.
5. `--parallel N` (1–8, default 2) runs up to N items at once; a value outside 1–8 is refused with a message and exit 1 before anything runs.
6. Two `artai generate` processes started on the same manifest at the same time never generate the same item: each item is claimed before work starts, and an item claimed by a live process is skipped by the other.
7. `--ids a,b,c` limits the run to those ids (an unknown id is refused before anything runs, naming it); `--reverse` works from the end of the list.
8. Every backend call's output is saved to a per-item log file in the work directory.
9. `--backend command` runs a command line given in the manifest (`artai.command`, with `{prompt}`, `{output}`, `{id}` placeholders) — the equivalent of GlobalHeadsOrTails' `cli` backend. The prompt is passed so that quotes or `;` in it cannot run extra shell commands.

## STORY-ART-3: Paint with the real providers we already use
**Points:** 5

**As an** operator,
**I want** to choose `codex`, `agy` or `gemini` as the image provider with one flag,
**so that** I can switch providers when one runs out of quota without changing the manifest.

### Acceptance Criteria
1. `--backend codex` invokes the Codex CLI in workspace-write sandbox mode, never with an approval/sandbox bypass flag, asking it to use its image tool (not to write drawing code) and save to the item's master path.
2. `--backend agy` invokes the Antigravity CLI; if the CLI saves its image somewhere other than the requested path, artai finds the newest matching file in the Antigravity scratch directory and moves it into place. A permission-bypass flag is only passed when `ARTAI_AGY_YOLO=1` and exactly one id is selected; otherwise the run is refused before starting.
3. `--backend gemini` calls the Gemini image API with `GEMINI_API_KEY` from the environment and model from `ARTAI_GEMINI_MODEL` (default `gemini-nano-banana-2.1`). If the key is unset, the run is refused before any item starts with a message naming the variable. The key never appears in logs, output or files.
4. A Gemini response that is not a PNG, or contains no image, is a failure for that item with the API's message (first 500 characters) in the item log; HTTP 429 or a quota message is treated as quota exhaustion (STORY-ART-2 AC 3).
5. An item may name a reference image (`reference_image` in its record). For `gemini` it is sent with the request; for `codex`/`agy` its path is added to the prompt as a likeness reference. A reference path that does not exist fails that item with the path in the message.
6. Each provider's quota wording ("quota", "usage limit", "rate limit", "429", "too many requests", "upgrade your plan") is recognised as quota exhaustion.

## STORY-ART-4: Turn masters into web-ready assets
**Points:** 3

**As an** operator shipping art inside an app,
**I want** `artai pack <manifest>` to turn the large masters into small, consistently framed web images in the set's output directory,
**so that** the repo carries only light assets and every image fits its slot.

### Acceptance Criteria
1. When the manifest does not say, `fit` is `autocrop` for YAML sets (GlobalHeadsOrTails behaviour) and `contain` for TSV/JSON lists (recard behaviour); `--fit` on the command line overrides both.
2. With `fit: contain` (recard behaviour), each master is resized so its longest edge equals `size` (default 512) with its aspect ratio preserved — a 1024×1536 master becomes 341×512.
3. With `fit: autocrop` (GlobalHeadsOrTails behaviour), the plain background margin is trimmed, the subject is centred on a canvas of exactly the set `resolution` with `pad` pixels of margin, filled with the original background colour.
4. Output format (`webp`, `png`, `jpeg`, default `webp`) and `quality` (default 88) come from the manifest or `--format`/`--quality`; files are named `<id>.<format>` (or the item's `output_filename`).
5. Masters that do not open are skipped and listed by id; the summary reports `packed X/Y` and the exit code is 1 if any were skipped. No existing output file is replaced by a partial write.

## STORY-ART-5: Review and prove a set is complete
**Points:** 3

**As an** art reviewer approving a set before it ships,
**I want** a contact sheet I can browse and a verify check that only passes when every image really exists,
**so that** "done" means done and missing or duplicate art is impossible to overlook.

### Acceptance Criteria
1. `artai review <manifest>` writes a single self-contained HTML page showing every item's packed image, id, name, metadata and final prompt, with a search box that filters by id or metadata; items without an image are visibly marked "missing".
2. The page opens correctly from disk (relative image paths) and prints its path on completion.
3. `artai verify <manifest>` exits 0 only when every item has a packed image that opens at the set's required size; otherwise it lists each missing/invalid id and exits 1.
4. `verify` reports any two items whose packed images are byte-identical, naming both ids, and exits 1.
5. With `--ids`, `verify` prints a line saying the result covers the selected sample only and cannot show the set is complete.

## STORY-ART-6: Replace a rejected image without losing it
**Points:** 2

**As an** art reviewer who rejected some images,
**I want** `artai regenerate <manifest> --ids x,y` to set aside the rejected images and paint new ones,
**so that** I can redo specific items without deleting anything by hand or losing the old versions.

### Acceptance Criteria
1. The current master and packed image for each selected id are moved into a timestamped `rejected/` folder in the work directory, then those items are generated again (same options as `generate`).
2. `regenerate` without `--ids` is refused with a message and exit 1; nothing is moved.
3. An id currently being generated by another live process is refused, naming it; nothing is moved for any id.
4. `artai unlock <manifest> --ids x` clears a claim left by a crashed run, but refuses (naming the id) when a live process still holds it.

## STORY-ART-7: Prove both existing projects can switch over
**Points:** 3

**As the** owner of recard and GlobalHeadsOrTails,
**I want** evidence that each project's current art inputs run through `artai` unchanged, plus written instructions for switching,
**so that** migrating them later is a mechanical change with no surprises.

### Acceptance Criteria
1. Copies of GlobalHeadsOrTails' four sticker manifests (`twelve-clans/manifest.yaml`, `fantasy-heroes/manifest.yaml`, `rangers-history/manifest.yaml`, `rangers-history/champions.yaml`, with their full data files) and a sample of recard's RTG job list are kept as test fixtures, and `artai status`, `prompts`, `generate --backend mock`, `pack`, `review` and `verify` succeed on each in the test suite.
2. For each GlobalHeadsOrTails fixture, `artai prompts` produces the same final prompt text as `tools/art_generator.py --export-prompts` does today (fixture of expected output captured from the source repo).
3. `docs/MIGRATION.md` gives, for each project, the replacement for every current art make target (recard `art-gen`, `art`; GlobalHeadsOrTails `art-status`, `art-generate`, `art-review`) and lists any behaviour that differs.
4. `docs/USAGE.md` documents every command, option, environment variable and manifest field, with one complete example manifest.

---

## Out of Scope
- Changing recard or GlobalHeadsOrTails (Makefiles, deleting their copies) — next sprint, per the owner.
- The Rangers catalog builder, NHL reference-photo fetching, sticker-pack activation and the sticker gallery web server — project-specific.
- Detached background "production lanes" with process supervision, and recording the provider's exact quota reset time.
- New providers beyond codex, agy, gemini, mock and command (e.g. OpenAI Images API, Stable Diffusion).
- Publishing artai as a package; a build/release channel.
- Image-level quality judgement (likeness, style consistency) — that remains human review.

## Open Questions
1. Should Trin run one live sample (one image) per real provider during UAT, spending a little quota? Owner decides. Assumed **no**: providers are verified with stand-ins; the owner runs a live sample when convenient.
2. ~~Should the `rangers-history` fixture be trimmed?~~ Closed at Gate 1: its `cards.json` has 143 records; fixtures keep the full files.
