# Agent State — Bob (coordinator checkpoint)

## Context
### Recent Decisions
- 2026-10-20 (owner): artai is **Python**; Sprint 1 = **build the tool only** (no changes to recard/GHOT); git = **commit per approved phase on `main`, never push**.
- Architecture decisions ADR-0001…0005 in `docs/DECISIONS.md` (Python port; masters→pack two stages; stdlib-only providers; per-item claim files; safe defaults: `--backend` required, codex sandboxed, no shell).

### Key Findings
- Source repos: `../recard` (`tools/imagegen/*.mjs`) and `../GlobalHeadsOrTails` (user wrote "GlobalHeadsAndTails"; folder is **GlobalHeadsOrTails**): `tools/art_generator.py` + deleted tools recoverable via `git show b6e4e7e^:tools/sticker_art.mjs` etc. Survey: `agents/oracle/art_tooling_survey.md`.
- artai is pip-installable from source (`pip install /path/to/artai`), verified in a clean venv; recorded in `docs/SDLC.md` §7.

### Important Notes
- Sprint 1 complete and launched 2026-10-20. Commits `86b1ea5`…`384d3d7` on `main` (13 commits), **none pushed**.
- 138 tests pass (`bobp make test`, ~47 s on this Pi; parity suite is most of it); `bobp make lint` clean.
- Real `codex` (/usr/bin/codex) and `agy` (~/.local/bin/agy) are installed; providers were only tested with stand-ins (no quota spent).
- Chat for Sprint 1 archived: `agents/chat_archive/CHAT_SPRINT_1.md`.
- **Uncommitted (left for owner on purpose):** the Bob Protocol scaffolding — `agents/`, `.agents`, `.claude/`, `.cursorrules`, `.github/`, `AGENT.md`, `AGENTS.md`, `CHATGPT.md`, `GEMINI.md`. All artai code/docs are committed.

## Current Task
**Status:** Completed — idle, awaiting owner decisions
**Assigned to:** Bob (coordination)
**Started:** 2026-10-20

### Task Description
Sprint 1: consolidate art generation tooling into `artai`; post-sprint Oracle groom, Tank SDLC pip-install update, Oracle re-review.

### Progress
- [x] Init, SDLC bootstrap (Tank), stories + arch (2 gate rounds each), 5 phases, sprint close, launch
- [x] Oracle groom (ARCH/ADR synced, README TOC, dead links removed) — `f9a85ac`
- [x] Tank: pip install documented in SDLC §7 + conformance item 10 — `daf8a68`; item 5 rescoped — `384d3d7`
- [x] Oracle re-review: rubric SDLC all ≥ A
- [ ] Owner decisions (see Next Steps)

### Blockers
None — waiting on owner.

### Oracle Consultations
Oracle state: `agents/oracle/state.md` (docs consistent as of 2026-10-20).

## Next Steps
### Immediate Next Action
On resume (`/init`): read this file, then `task.md` (Sprint 1, all ticked) and `docs/BACKLOG.md`. Ask the owner which of these to do — do not start any unasked:
1. **Release 0.2.0?** If yes (Cypher + Tank): set `version = "0.2.0"` in `pyproject.toml` AND `__version__` in `src/artai/__init__.py`; move CHANGELOG "Unreleased" to `## 0.2.0 — <date>`; `bobp make test && bobp make lint`; commit `chore(release): 0.2.0`; `git tag v0.2.0`. Do not push.
2. **Live provider samples?** If yes (Trin): one image each, e.g. `.venv/bin/artai generate tests/fixtures/recard/rtg_jobs.tsv --backend codex --ids rtg-b-001 --work <scratch>`; same with `--backend agy`; gemini only if `GEMINI_API_KEY` is set. Record results in `docs/sprints/UAT_PLAN_SPRINT1.md` §5.
3. **Migration sprint?** If yes: run `$sprint` for backlog #1 using the checklist at the end of `docs/MIGRATION.md` (edits recard + GlobalHeadsOrTails Makefiles; needs owner OK to change those repos).
4. **Commit the agent scaffolding?** Owner's call (listed above).

### Waiting On
Owner answers to 1–4.

### Planned Work
- [ ] Backlog items 3–7 in `docs/BACKLOG.md` (reference-image preflight warning, faster test target, fixture refresh, non-POSIX, quota reset time)
