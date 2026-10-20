# Sprint 2: Move recard and GlobalHeadsOrTails onto artai

*   **Tier**: 2 (maintenance; combined stories + architecture by Cypher & Morpheus)
*   **Total Points**: 13
*   **Source**: User, 2026-10-20: "migrate recard and GlobalHeadsVsTails to use artai" + "and remove all old docs and refs". Owner decisions the same day: commit GlobalHeadsOrTails' uncommitted work too; install artai with pip into each repo; delete everything that mentions the old tools; commit per phase on each repo's current branch (recard `dev`, GlobalHeadsOrTails `main`), never push.
*   **Repos changed**: `../recard`, `../GlobalHeadsOrTails` (= "GlobalHeadsVsTails"), and artai docs.
*   **Status**: Approved by Smith (round 2) — see agents/CHAT.md

## Goal

Both projects produce their art through artai, and nothing in either repo still describes,
tests or calls the old tools (`recard/tools/imagegen`, GlobalHeadsOrTails
`tools/art_generator.py` and its predecessors). Existing finished masters are reused, so the
switch costs no generation quota.

## Assumptions made for the owner

1. **"Delete everything that mentions them"** means: files *about* the old tools are deleted; files that are about something else (DECISIONS.md, SDLC.md, chat logs, agent notes, task boards) have the mentioning lines/sections removed, not the whole file. If wrong: whole files go too (git keeps them).
2. artai keeps its own design history (ARCH, ADRs, LESSONS, CHANGELOG) that names where it came from; artai's *plan* documents about the old tools (`docs/MIGRATION.md`, `agents/oracle/art_tooling_survey.md`) are deleted once this sprint lands. The GHOT/recard input fixtures in `tests/fixtures/` stay — they are the projects' manifests, not the old tools.
3. artai is installed **editable** (`pip install -e ../artai`), so a change in the sibling checkout is picked up without reinstalling; the repos expect artai at `../artai` (overridable with `ARTAI_SRC=`).
4. GlobalHeadsOrTails' pre-existing uncommitted work (tag_validator changes, the `install-all` pip→pipx line, untracked agent files) is committed **unchanged** in its own commit before any migration change, even though `pipx install -e <libs>` looks wrong. It is reported, not fixed.
5. GlobalHeadsOrTails is 1 commit behind `origin/main` (agent notes only). We do not pull; the owner reconciles when pushing.

---

## STORY-MIG-1: recard paints and packs card art with artai
**Points:** 4

**As the** recard maintainer, **I want** `make art-gen` / `make art` to run artai, **so that** recard uses the shared, safer tool and I stop maintaining its own copy.

### Acceptance Criteria
1. `make art-install` creates `.venv` if missing and runs `.venv/bin/pip install -e ../artai`; if `../artai` (or `$ARTAI_SRC`) does not exist it stops with one line naming the path and how to fix it.
2. `make art-gen` regenerates the RTG job list and runs `artai generate` with `--backend codex --parallel 4 --retries 1`, the same style text as today, work dir `build/rtg-art`. With the 132 existing masters moved to `build/rtg-art/masters/`, it reports `0 generated, 132 already present` and calls codex zero times.
3. `make art` runs `artai pack` into `assets/cards/rtg` at size 512, quality 82; every packed file keeps its current dimensions (e.g. 341×512).
4. `make art-review` and `make art-verify` exist and call `artai review` / `artai verify` on the same job list.
5. `make help` lists the art targets with their new meaning; `npm run cards:art` is removed.
6. recard's gate `make check-fast` still passes.

## STORY-MIG-2: GlobalHeadsOrTails generates stickers with artai
**Points:** 4

**As the** GlobalHeadsOrTails maintainer, **I want** the `art-*` targets to run artai, **so that** sticker sets get resume, quota stops, real providers and a verify gate.

### Acceptance Criteria
1. Before any migration change, the repo's pre-existing uncommitted work is committed unchanged in one commit; the commit message says it is pre-existing work committed at the owner's request.
2. `make install-art` creates the root `.venv` if missing (the SDLC's standard environment) and runs `.venv/bin/pip install -e ../artai`; missing `../artai` fails with one line naming the path.
3. `make art-status`, `art-generate`, `art-review` keep their names and `MANIFEST=` default (twelve-clans); new `art-pack` and `art-verify`. `art-generate` needs `BACKEND=` (no default; omitted → artai's message listing choices) and runs generate then pack.
4. Existing masters are reused: the 36 twelve-clans masters, and the rangers masters whose ids are in `rangers-history/manifest.yaml` (90) and `champions.yaml` (37), are copied into the artai work dirs; `make art-status` for twelve-clans shows `masters: 36`.
5. `make test-all` no longer runs the old art tests and the remaining suites' result is unchanged from before the migration.

## STORY-MIG-3: No trace of the old tools
**Points:** 5

**As the** owner, **I want** every old tool, test, doc and reference removed, **so that** nobody follows stale instructions.

### Acceptance Criteria
1. Deleted: recard `tools/imagegen/`, `tests/imagegen.test.js`; GHOT `tools/art_generator.py`, `tools/tests/test_art_generator.py`, and documents dedicated to the old tools (e.g. `agents/oracle.docs/art_generator_guide.md`, `agents/morpheus.docs/arch_art_generator.md`, `agents/cypher.docs/art_generator_sprint.md`, `art_generator_groom_Summary…`).
2. In each repo this returns nothing (tracked files):
   ```sh
   git grep -nE 'imagegen|art_generator|sticker_art|STICKER_ART|nanobanana|sticker_production|sticker-production|rtg-art-raw|cards:art|test-art-generator|rangers-reference-index|sticker-art-(manifest|generate|pack|verify|review|unlock|regenerate|activate|references)'
   ```
   The live `sticker-art-gallery` target and `tools/sticker_gallery.py` are not old tools and stay.
3. Each repo's live docs (recard README/RTG_DESIGN, GHOT SDLC/COLLECTABLES, task boards) describe the artai targets instead, in one short section each.
4. artai: `docs/MIGRATION.md` and `agents/oracle/art_tooling_survey.md` deleted; README/BACKLOG/CHANGELOG say the migration is done.

## Out of scope
- Spending generation quota (no live provider runs).
- Pushing any repo; pulling GHOT's 1 upstream commit.
- Fixing GHOT's `install-all` pipx line or its tag_validator work.

---

## Architecture (Morpheus)

**Boundary.** artai stays a sibling checkout; each consumer pip-installs it (editable) into its
own `.venv` and calls `.venv/bin/artai` from Makefile targets. No consumer code imports artai —
the contract is the CLI (docs/USAGE.md) and exit codes 0/1/2.

```
recard/Makefile ──art-install──▶ .venv (pip -e ../artai) ──▶ .venv/bin/artai generate|pack|review|verify
GHOT/Makefile   ──install-art──▶ .venv (pip -e ../artai) ──▶ .venv/bin/artai status|generate|pack|review|verify
```

**Makefile shape (both repos).**
```make
ARTAI_SRC ?= ../artai
ARTAI     := .venv/bin/artai
art-install:                       # GHOT: install-art
	@test -d "$(ARTAI_SRC)" || { echo "artai not found at $(ARTAI_SRC) - clone it there or set ARTAI_SRC=<path>"; exit 1; }
	test -x .venv/bin/python || python3 -m venv .venv
	.venv/bin/pip install -q -e "$(ARTAI_SRC)"
```
Art targets depend on the install target, which is idempotent (pip no-ops when satisfied).

**Revision (Phase 2, Morpheus).** GlobalHeadsOrTails' Makefile switches *every* Python target to
the root `.venv` as soon as it exists. Creating it with only artai inside would silently move
`test-all` etc. to an environment without pytest. So GHOT installs artai into a dedicated
`.venv-art/` (gitignored) and calls `.venv-art/bin/artai`; recard keeps its shared `.venv`
(only `test-audit` uses it, via explicit paths). STORY-MIG-2 AC2 reads `.venv-art` accordingly.

**Work dirs and masters.** recard: `--work build/rtg-art` (masters `build/rtg-art/masters/`).
GHOT: manifests set no `work_dir`, so artai's default `build/artai/<set name>` applies
(`twelve_clans`, `fantasy_heroes`, `rangers_targets`, `rangers_champions`). One-time master
seeding is a file copy done during the sprint (build dirs are gitignored; no code or target).
Old build dirs (`build/rtg-art-raw`, `build/sticker-art`, `build/rangers-art`) are left in
place for the owner to delete.

**Failure modes.** Missing `../artai` → one-line message, exit 1. Quota → artai exit 2 propagates
through make. Missing `BACKEND` → artai's own message. Pack of a missing master → artai lists it.

**Build-environment check.** recard: adds a Python dependency to its existing `.venv` (already
used by `test-audit`) — documented in README. GHOT: uses the SDLC's root `.venv`; adds artai as
an editable sibling install — a mechanism change recorded in GHOT `docs/SDLC.md` §2 by Tank.
artai itself: no change. No Tank Phase 0 needed beyond committing GHOT's pre-existing work.

**Decisions.** ADR-0006 (artai): consumers install artai editable from a sibling checkout via
their own Makefile install target (alternatives: path to artai's venv — rejected by owner;
`git+` URL — not possible until artai is pushed).
