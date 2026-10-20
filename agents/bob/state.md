# Agent State — Bob (coordinator checkpoint)

## Context
### Recent Decisions
- 2026-10-20 (owner): artai is **Python**; Sprint 1 = **build the tool only** (no changes to recard/GHOT); git = **commit per approved phase on `main`, never push**.
- Architecture decisions ADR-0001…0005 in `docs/DECISIONS.md` (Python port; masters→pack two stages; stdlib-only providers; per-item claim files; safe defaults: `--backend` required, codex sandboxed, no shell).

### Key Findings
- Source repos: `../recard` (`tools/imagegen/*.mjs`) and `../GlobalHeadsOrTails` (user wrote "GlobalHeadsAndTails"; folder is **GlobalHeadsOrTails**): `tools/art_generator.py` + deleted tools recoverable via `git show b6e4e7e^:tools/sticker_art.mjs` etc. (Survey doc deleted in Sprint 2; see git history.)
- artai is pip-installable from source (`pip install /path/to/artai`), verified in a clean venv; recorded in `docs/SDLC.md` §7.

### Important Notes
- 2026-10-20 Sprint 2 DONE: recard (dev a1c6fc5) and GlobalHeadsOrTails (main 666b617 pre-existing work, 35fb018 migration) use artai via `make art-install` / `make install-art` (pip -e ../artai). Old tools/docs/refs removed (grep-verified). artai e7acfbf. Nothing pushed in any repo; GHOT is also 1 commit behind origin/main.
- Sprint 1 complete and launched 2026-10-20. Commits `86b1ea5`…`384d3d7` on `main` (13 commits), **none pushed**.
- 138 tests pass (`bobp make test`, ~47 s on this Pi; parity suite is most of it); `bobp make lint` clean.
- Real `codex` (/usr/bin/codex) and `agy` (~/.local/bin/agy) are installed; providers were only tested with stand-ins (no quota spent).
- Chat for Sprint 1 archived: `agents/chat_archive/CHAT_SPRINT_1.md`.
- Agent scaffolding committed (35b5c40); working tree clean.

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
On resume: ask the owner (do not start unasked):
1. Push? artai main, recard dev, GlobalHeadsOrTails main (GHOT needs `git pull --rebase` first: 1 upstream commit). Agents are blocked from `git push` by the permission classifier; the owner runs `! git push ...`.
2. Release artai 0.2.0 + tag (CHANGELOG has Sprint 1 + 2 under Unreleased).
3. Live provider sample (recard: `make art-gen` uses sandboxed codex — never run live yet).
4. Backlog #9/#10 in docs/BACKLOG.md (protect packed-without-master; pack skips placeholders).

### Waiting On
Owner answers to 1–4.

### Planned Work
- [ ] Backlog items 3–7 in `docs/BACKLOG.md` (reference-image preflight warning, faster test target, fixture refresh, non-POSIX, quota reset time)
