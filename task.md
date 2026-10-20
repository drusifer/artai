# Sprint 1 Task Board: One art tool for every project

*   **Goal**: Deliver the `artai` CLI that consolidates recard's and GlobalHeadsOrTails' art pipelines (manifest → resumable generation → pack → review/verify → regenerate). Prove both projects' current inputs run through it unchanged and document how to switch.
*   **Tier**: Tier 1 (Major)
*   **Total Points**: 24
*   **Branch**: `main` (per `docs/SDLC.md` §6 — one commit per approved phase, never push)
*   **Stories**: `docs/sprints/USER_STORIES_SPRINT1.md` · **Architecture**: `docs/ARCH.md` · **Decisions**: `docs/DECISIONS.md`
*   **Status**: Approved (Morpheus Step 3a) — Phase 1 in progress

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** Verify `docs/SDLC.md` exists and is current. (*Owner: Mouse | Verification: `test -f docs/SDLC.md`*) — written by Tank, commit 86b1ea5.

Phase 0 (build environment) is not needed: Morpheus's arch §7 flags no new language, package manager or tool.

---

## Sprint Execution Phases

Each phase ends with: Trin UAT (`bobp make test && bobp make lint` + the phase's ACs) → Morpheus review → commit on `main`.

### Phase 1: Manifests, prompts and status (STORY-ART-1, fixtures for ART-7)
*Phase goal: `artai prompts` and `artai status` work on every manifest kind, with parity fixtures in place.*
- [x] **Task 1.1:** Capture parity fixtures: copy GHOT's 4 manifests + data files and a recard RTG job-list sample into `tests/fixtures/`; record GHOT `--export-prompts` output for each as expected JSON. (*Owner: Neo | Verification: `ls tests/fixtures/ghot tests/fixtures/recard`*)
- [x] **Task 1.2:** TDD `manifest.py` (YAML inline/data_file, TSV, JSON; validation; defaults; `--work/--out/--style/--fit` overrides) and `prompts.py` (GHOT semantics, missing-placeholder warnings); `cli.py` with `prompts` and `status`. (*Owner: Neo | Verification: `bobp make test ARGS="-k 'manifest or prompts or status'"`*)
- [x] **Task 1.3:** UAT ART-1 AC1–7 + ART-7 AC2 parity; Morpheus review; commit. (*Owner: Trin → Morpheus | Verification: `bobp make test && bobp make lint`*)

### Phase 2: Resumable generation engine (STORY-ART-2 AC1–8)
*Phase goal: `artai generate --backend mock` is resumable, quota-terminal, parallel and safe across processes.*
- [x] **Task 2.1:** TDD `imaging.py` (is_valid by dimensions, placeholder tag, atomic save), `claims.py` (exclusive claims, liveness, stale takeover), `backends/base.py` + registry + `mock`, `backends/_proc.py` (argv run, timeout, log, quota regex). (*Owner: Neo | Verification: `bobp make test ARGS="-k 'imaging or claims or backend'"`*)
- [x] **Task 2.2:** TDD `runner.py` + `generate` CLI: skip/resume, retries, timeout, quota stop + marker + exit 2, `--parallel` bounds, `--ids`/`--reverse`, per-item logs, required `--backend`, two concurrent processes. (*Owner: Neo | Verification: `bobp make test ARGS="-k 'runner or generate'"`*)
- [x] **Task 2.3:** UAT ART-2 AC1–8 (incl. a real two-process run on a fixture); Morpheus review; commit. (*Owner: Trin → Morpheus | Verification: `bobp make test && bobp make lint`*)

### Phase 3: Real providers (STORY-ART-2 AC9, STORY-ART-3)
*Phase goal: `command`, `codex`, `agy` and `gemini` backends work against stand-in executables and a stub HTTP server.*
- [ ] **Task 3.1:** TDD `command` backend (shlex, per-argv substitution, `{output}`/`{output_path}`/`{resolution}`, `cli_command` alias, injection test) and `codex` + `agy` backends (safe flags, scratch claim, yolo rule, reference clause) using fake CLIs in a temp dir. (*Owner: Neo | Verification: `bobp make test ARGS="-k 'command or codex or agy'"`*)
- [ ] **Task 3.2:** TDD `gemini` backend against a local stub HTTP server (missing key preflight, PNG signature, no-image error, 429 → quota, reference image sent, key never logged). (*Owner: Neo | Verification: `bobp make test ARGS="-k gemini"`*)
- [ ] **Task 3.3:** UAT ART-2 AC9 + ART-3 AC1–6; Morpheus review (security focus: no shell, no key leakage, no bypass flags); commit. (*Owner: Trin → Morpheus | Verification: `bobp make test && bobp make lint`*)

### Phase 4: Pack, review and verify (STORY-ART-4, STORY-ART-5)
*Phase goal: masters become packed assets, a browsable contact sheet, and a verify gate that means "done".*
- [ ] **Task 4.1:** TDD `pack.py` (contain/autocrop fit, defaults per kind, format/quality, atomic writes, skip+list unopenable) + `pack` CLI. (*Owner: Neo | Verification: `bobp make test ARGS="-k pack"`*)
- [ ] **Task 4.2:** TDD `review.py` contact sheet (escaped, relative paths, search, missing marked) and `verify` (size, sha256 duplicates, placeholder rule + `--allow-mock`, sample-only notice) + CLIs. (*Owner: Neo | Verification: `bobp make test ARGS="-k 'review or verify'"`*)
- [ ] **Task 4.3:** UAT ART-4 AC1–5 + ART-5 AC1–5 (open the HTML once); Morpheus review; commit. (*Owner: Trin → Morpheus | Verification: `bobp make test && bobp make lint`*)

### Phase 5: Regenerate, parity end-to-end and docs (STORY-ART-6, STORY-ART-7)
*Phase goal: rejected art can be redone safely, every fixture runs the full pipeline, and switching is documented.*
- [ ] **Task 5.1:** TDD `regenerate` (archive to `rejected/<ts>/`, all-or-nothing live-claim refusal, requires `--ids`) and `unlock` (refuse live). (*Owner: Neo | Verification: `bobp make test ARGS="-k 'regenerate or unlock'"`*)
- [ ] **Task 5.2:** Parity end-to-end test over all fixtures (status → prompts → generate mock → pack → review → verify `--allow-mock`); write `docs/USAGE.md` and `docs/MIGRATION.md`. (*Owner: Neo | Verification: `bobp make test ARGS="-k parity"`*)
- [ ] **Task 5.3:** UAT ART-6 AC1–4 + ART-7 AC1–4 + sprint UAT plan `docs/sprints/UAT_PLAN_SPRINT1.md`; Morpheus review; commit. (*Owner: Trin → Morpheus | Verification: `bobp make test && bobp make lint`*)

---

## Stage 3: Sprint Closeout

- [ ] **Task C.1:** SDLC conformance check. (*Owner: Tank | Verification: `bobp make distclean && bobp make install && bobp make test && bobp make lint`*)
- [ ] **Task C.2:** Document grooming, lesson archiving, and chat report. (*Owner: Oracle | Verification: `bobp chat-report --moniker SPRINT_1`*)
- [ ] **Task C.3:** End-to-end user usability testing & lesson review. (*Owner: Smith | Verification: `bobp chat "*user approve"`*)
- [ ] **Task C.4:** Sprint retrospective & backlog grooming. (*Owner: All personas | Verification: Retros posted in CHAT.md*)
- [ ] **Task C.5:** Sprint launch & release announcement (version 0.1.0 → 0.2.0 with user approval). (*Owner: Cypher | Verification: `bobp chat "*pm launch"`*)
