# Migrating recard and GlobalHeadsOrTails to artai

Status: **ready, not yet applied** — Sprint 1 built artai and proved both projects' current
inputs run through it unchanged (`tests/test_parity.py`, `tests/test_prompts.py`). Switching the
projects over is a later sprint. Commands below assume artai is checked out beside them
(`../artai`) and installed (`make -C ../artai install`); define in each Makefile:

```make
ARTAI ?= ../artai/.venv/bin/artai
```

---

## GlobalHeadsOrTails

Manifests (`game_server/src/game_server/sticker_catalog/*/manifest.yaml`, `champions.yaml`) are
used **as they are** — no edits. All four produce prompts identical to
`tools/art_generator.py --export-prompts` (273 of 273 items).

| Today | With artai |
|---|---|
| `make art-status MANIFEST=m.yaml` | `$(ARTAI) status m.yaml` |
| `make art-generate MANIFEST=m.yaml BACKEND=mock` | `$(ARTAI) generate m.yaml --backend mock && $(ARTAI) pack m.yaml` |
| `make art-generate MANIFEST=m.yaml BACKEND=cli` | `$(ARTAI) generate m.yaml --backend command && $(ARTAI) pack m.yaml` |
| *(real provider — previously the deleted `sticker_art.mjs`)* | `$(ARTAI) generate m.yaml --backend codex` (or `agy`, `gemini`) then `pack` |
| `make art-review MANIFEST=m.yaml` | `$(ARTAI) review m.yaml` |
| `art_generator.py --export-prompts` | `$(ARTAI) prompts --json m.yaml` |
| `art_generator.py --item ID` | `--ids ID` (comma-separated list allowed) |
| `art_generator.py --force` | `$(ARTAI) regenerate m.yaml --ids A,B --backend …` (old images are archived, not overwritten) |
| `make test-art-generator` | `make -C ../artai test` |
| `sticker-art-verify` (old, deleted) | `$(ARTAI) verify m.yaml` |
| `sticker-art-unlock` (old, deleted) | `$(ARTAI) unlock m.yaml --ids …` (rarely needed: dead claims are taken over) |
| production lanes (`sticker_production.py`, deleted) | run several `artai generate` processes (e.g. one with `--reverse`); claims keep them apart |

### Behaviour differences

1. **Two steps.** `generate` now keeps a full-size master in `work_dir/masters/` and `pack`
   writes the 512px WebP. Re-packing never costs quota. Default `work_dir` is
   `build/artai/<set name>` (set `work_dir:` in the manifest to choose).
2. **`--backend` is required.** The old default was `mock`.
3. **Mock art is labelled.** Mock masters are tagged as placeholders: real backends replace
   them, and `verify` fails on them unless `--allow-mock`.
4. **`cli_command` runs without a shell.** Placeholders `{prompt}`, `{id}`, `{output_path}`
   (alias `{output}`) and `{resolution}` still work, but pipes, redirects and `&&` no longer do;
   put such logic in a script. A prompt can no longer inject shell commands.
5. **`autocrop: false`** used to stretch the image to `resolution`; it now means
   `fit: contain` (aspect kept, longest edge = `size`). None of the four manifests use it.
6. **Ids must be file-safe** (letters, digits, `.`, `-`, `_`); the old tool rewrote other
   characters to `_`. All current ids already comply.
7. **`families`/`forms` data files** are no longer expanded automatically; all current
   `cards.json` files are flat lists.
8. **Resume** checks masters by image size (≥ `min_size`, default 512), not by "file exists".
9. **`resolved_prompt`** is called `prompt` in `prompts --json` output.

### Existing generated art

The shipped WebPs in `static/stickers/` are untouched by `status`/`review`/`verify` (they read
them). To regenerate on top of them without masters, run `generate` + `pack` as usual — `pack`
overwrites the WebP only after a new master exists. The 479 Rangers masters left in
`build/rangers-art/raw/*.png` (from the old 1,162-player run) can seed artai: copy them to
`build/artai/rangers_targets/masters/` (same `<id>.png` names). As of 2026-10-20, 90 of them
match ids in `rangers-history/manifest.yaml` and 37 match `champions.yaml`; `generate` skips
those and ignores the rest.

---

## recard

The RTG job list (`npm run cards:jobs` → TSV) is used **as it is**.

| Today | With artai |
|---|---|
| `make art-gen` | `npm run cards:jobs > build/rtg-art-jobs.tsv` then `$(ARTAI) generate build/rtg-art-jobs.tsv --work build/rtg-art --backend codex --parallel 4 --retries 1 --style "high fantasy oil painting, Magic-the-Gathering card art, no text, no borders, no watermark"` |
| `make art` (`cards:art`) | `$(ARTAI) pack build/rtg-art-jobs.tsv --work build/rtg-art --out assets/cards/rtg --quality 82` |
| `node tools/imagegen/cli.mjs gen --backend agy` | `--backend agy` |
| `tests/imagegen.test.js` | covered by artai's test suite; delete with `tools/imagegen/` |

### Behaviour differences

1. **codex runs sandboxed.** recard passed `--dangerously-bypass-approvals-and-sandbox`; artai
   runs `codex exec --sandbox workspace-write` in the masters folder. Do one live sample
   (`--ids rtg-b-001`) before a full run to confirm image generation works in that mode.
2. **Masters folder.** recard wrote masters straight into `build/rtg-art-raw/`; artai uses
   `<work>/masters/`. Move existing masters: `mkdir -p build/rtg-art/masters && mv build/rtg-art-raw/*.png build/rtg-art/masters/`.
3. **Retries.** recard `--retries 2` meant two attempts in total; artai `--retries N` means
   N extra attempts. `--retries 1` matches recard's old default.
4. **Defaults.** `--parallel` default is 2 (was 3); packed quality default for lists is 88
   (recard used 82 — pass `--quality 82` to keep file sizes identical).
5. **Pack scope.** `pack` converts only items in the manifest (recard packed every image file in
   the folder).
6. **Quota marker** is `<work>/.quota-exhausted` (was inside the raw folder). Exit code 2 is unchanged.
7. **agy** no longer always passes `--dangerously-skip-permissions`; it needs
   `ARTAI_AGY_YOLO=1` and exactly one `--ids`.

---

## Checklist for the migration sprint

- [ ] Add `ARTAI ?= ../artai/.venv/bin/artai` and replace the targets above in each Makefile.
- [ ] Move existing masters into the artai work folder (see above).
- [ ] One live sample per provider actually used (codex for recard; codex/agy/gemini for GHOT).
- [ ] Delete `recard/tools/imagegen/`, `recard/tests/imagegen.test.js`,
      `GlobalHeadsOrTails/tools/art_generator.py`, `tools/tests/test_art_generator.py`.
- [ ] Update each project's `docs/SDLC.md` (new external tool dependency on artai).
