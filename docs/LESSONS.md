# artai — Lessons

Engineering lessons, newest first. Recorded by Oracle; reviewed by Smith at sprint close.

---

## [2026-10-20] When adding a venv to a repo whose Makefile auto-detects `.venv`, use a separate directory

> **Tags:** #Build #Makefile #Morpheus

### Context
Sprint 2 had to pip-install artai into GlobalHeadsOrTails. Its SDLC names a root `.venv` as the standard, so the plan said "install into the root `.venv`".

### The Issue
The Makefile picks `PYTHON` with `ifneq ($(wildcard .venv/bin/python),)` — the first time a root `.venv` exists, **every** Python target uses it. No root `.venv` existed; tests ran from `ntag424_sdm_provisioner/.venv`. Creating `.venv` with only artai in it would have silently moved `test-all` to an interpreter without pytest. Morpheus caught it reading the Makefile header before Phase 2.

### The Solution
A dedicated `.venv-art/` (gitignored) for artai, called by path (`.venv-art/bin/artai`); the workspace interpreter selection is untouched. recard kept its shared `.venv`, because there only `test-audit` uses it, by explicit path.

### The Rule (The "Lesson")
Before creating any virtualenv in a repo, grep its Makefile for `wildcard .venv` / `PYTHON ?=`. If interpreter selection depends on the directory existing, install the new tool into its own directory and call it by path.

### References
- **Commit:** GlobalHeadsOrTails `35fb018`; ADR-0006
- **Files:** GlobalHeadsOrTails `Makefile` (lines 1–7, `install-art`)

---

## [2026-10-20] When asked to "commit all changes" in someone else's working tree, dry-run and scan first

> **Tags:** #Git #Security #Tank

### Context
The owner asked for GlobalHeadsOrTails' pre-existing uncommitted work to be committed with the migration.

### The Issue
`git add -A --dry-run` showed an untracked `ntag424_sdm_provisioner/dist/sdm-provisioner-latest.tar` (434 MB container image; GitHub rejects files > 100 MB) that also matched a private-key pattern. A blind `git add -A` would have put it into history.

### The Solution
Paused and asked; the owner chose to skip `dist/` and `build/` and gitignore them. Then committed the rest (149 files) after a size and secret scan of the staged set.

### The Rule (The "Lesson")
Before committing a working tree you did not create, run `git add -A --dry-run`, check sizes (`du` on untracked files) and grep the staged set for key patterns. Anything over 50 MB or matching a secret pattern goes back to the owner before it is staged.

### References
- **Commit:** GlobalHeadsOrTails `666b617`
- **Files:** GlobalHeadsOrTails `.gitignore`

---

## [2026-10-20] When consolidating tools, recover deleted predecessors from git history first

> **Tags:** #Process #Consolidation #Oracle

### Context
Sprint 1 consolidated art tooling from recard and GlobalHeadsOrTails. The obvious sources were
recard `tools/imagegen/` and GHOT `tools/art_generator.py`.

### The Issue
GHOT's live `art_generator.py` was a refactor that had *dropped* production features: no resume
validation, no quota handling, no parallelism, no real providers. The features existed only in
files deleted by commit `b6e4e7e` (`tools/sticker_art.mjs`, `nanobanana_backend.mjs`,
`sticker_production.py`). Evidence of them was in `build/rangers-art/` (quota report, lane locks,
1,162-item manifest) that the live tool could not have produced.

### The Solution
`git log --diff-filter=D --name-only` in each source repo, then `git show <commit>^:<path>` for
each deleted art tool. Their behaviour (claims, codex-safe, Gemini API, verify, regenerate)
became Stories ART-2/3/5/6.

### The Rule (The "Lesson")
Before scoping a consolidation, for each source repo run
`git log --all --diff-filter=D --name-only --format= | grep -i <topic>` and compare the build
output on disk with what the live code can produce. Anything on disk the live code cannot make
points at deleted or out-of-tree tooling that belongs in scope.

### References
- **Commit:** GHOT `b6e4e7e`; artai `39a01eb`
- **Files:** `docs/sprints/USER_STORIES_SPRINT1.md` (the survey itself was removed in Sprint 2)

---

## [2026-10-20] When a provider runs in its own process group, Ctrl-C must kill it explicitly

> **Tags:** #Concurrency #Subprocess #Neo #Trin

### Context
`_proc.run_logged` starts providers with `start_new_session=True` so a timeout can kill the
provider *and* its children with `os.killpg`.

### The Issue
A new session also means the terminal's SIGINT never reaches the provider. On Ctrl-C the main
thread raised `KeyboardInterrupt`, but `ThreadPoolExecutor.__exit__` then waited for workers,
which waited on providers for up to `--timeout` (600 s). Trin found it in Phase 2 UAT; the mock
backend was too fast to show it, so the first attempt "passed" (`exit=0`) without testing anything.

### The Solution
Track running `Popen` objects; on `KeyboardInterrupt` set a stop event, `kill_all()` process
groups, shut the pool down, exit 130. Tested through the real CLI with a 60 s stand-in provider:
`tests/test_providers.py::test_ctrl_c_stops_quickly_and_releases_claims` (< 10 s, no claims left).

### The Rule (The "Lesson")
Whenever a child is started with `start_new_session=True` (or `setsid`), also register it so the
parent's interrupt handler can `killpg` it, and test interruption with a provider that sleeps —
never with an instant fake, which cannot show the hang.

### References
- **Commit:** `c33ecba`
- **Files:** `src/artai/backends/_proc.py`, `src/artai/runner.py`

---

## [2026-10-20] When taking over a stale lock file, check-delete-recreate must be one critical section

> **Tags:** #Concurrency #Locks #Morpheus

### Context
Item claims are `claims/<id>.lock`, created atomically with `os.link`. A claim whose owner process
is dead is "stale" and may be taken over.

### The Issue
The first version did: link fails → read claim → owner dead → `unlink` → link again. Two
processes that both read the same dead claim could interleave so the second `unlink` removed the
first one's *new* claim, and both generated the same item (spending quota twice). Found in
Morpheus's Phase 2 review, not by tests.

### The Solution
Takeover runs under `fcntl.flock` on `claims/.takeover`, re-checks liveness inside the lock, then
removes and re-links. Normal (non-stale) claiming stays lock-free.
Test: `tests/test_claims.py::test_concurrent_takeover_of_stale_claim_has_one_winner` (20 rounds × 4 threads).

### The Rule (The "Lesson")
For any "if stale then delete and recreate" on a shared file, put the re-check, delete and
recreate inside one lock; a check done before taking the lock does not count.

### References
- **Commit:** `c33ecba`
- **Files:** `src/artai/claims.py`, ADR-0004 in `docs/DECISIONS.md`
