# Sprint 2 Task Board: Move recard and GlobalHeadsOrTails onto artai

*   **Goal**: recard and GlobalHeadsOrTails make their art through artai (pip-installed into each repo), reusing existing masters, and every old tool, test, doc and reference is gone.
*   **Tier**: Tier 2 (Minor/Fast-track)
*   **Total Points**: 13
*   **Branch**: recard `dev`, GlobalHeadsOrTails `main`, artai `main` — one commit per approved phase per repo, never push.
*   **Plan**: `docs/sprints/SPRINT2_MIGRATION.md` (stories + architecture). Sprint 1: git history and `agents/chat_archive/CHAT_SPRINT_1.md`.
*   **Status**: Approved (Morpheus Step 3a) — in progress

---

## Stage 0: SDLC Gate (Blocker)

- [x] **Task 0.1:** `docs/SDLC.md` exists (artai). GHOT has `docs/SDLC.md`; recard has none (changes documented in its README). (*Owner: Mouse*)

### Phase 0: Pre-existing GlobalHeadsOrTails work (*Tank*)
- [x] **Task 0.2:** GHOT test baseline recorded; pre-existing work committed unchanged (`666b617`), except `ntag424_sdm_provisioner/dist` + `/build`, now gitignored (owner decision). (*Owner: Tank*)

## Sprint Execution Phases

### Phase 1: recard on artai (STORY-MIG-1, MIG-3 for recard)
- [x] **Task 1.1:** Makefile `art-install`/`art-gen`/`art`/`art-review`/`art-verify`; remove `cards:art`; move 132 masters to `build/rtg-art/masters`. (*Owner: Neo | `make art-gen` → 132 already present*)
- [x] **Task 1.2:** Delete `tools/imagegen`, `tests/imagegen.test.js`; scrub all references; README/RTG_DESIGN artai section. (*Owner: Neo | MIG-3 AC2 grep empty*)
- [x] **Task 1.3:** UAT (art targets, pack dimensions unchanged, `make check-fast`), Morpheus review, commit on `dev`. (*Owner: Trin → Morpheus*)

### Phase 2: GlobalHeadsOrTails on artai (STORY-MIG-2, MIG-3 for GHOT)
- [x] **Task 2.1:** Makefile `install-art`/`art-*`; drop old art tests from `test-all`; seed masters; Tank updates GHOT SDLC §2. (*Owner: Neo + Tank | `make art-status` → masters 36*)
- [x] **Task 2.2:** Delete old tool, tests and dedicated docs; scrub references everywhere else. (*Owner: Neo | MIG-3 AC2 grep empty*)
- [x] **Task 2.3:** UAT (targets; suites vs baseline), Morpheus review, commit on `main`. (*Owner: Trin → Morpheus*)

### Phase 3: artai cleanup (STORY-MIG-3 AC4) + ADR-0006
- [x] **Task 3.1:** Delete artai `docs/MIGRATION.md` and the survey; update README/USAGE/BACKLOG/CHANGELOG/doc index; record ADR-0006. (*Owner: Oracle*)
- [x] **Task 3.2:** Review + commit. (*Owner: Morpheus*)

## Stage 3: Sprint Closeout
- [ ] **Task C.1:** SDLC check (artai full; consumer art targets run). (*Owner: Tank*)
- [ ] **Task C.2:** Groom + chat report SPRINT_2. (*Owner: Oracle*)
- [ ] **Task C.3:** End-to-end user test across both repos. (*Owner: Smith*)
- [ ] **Task C.4:** Retro. (*Owner: All*)
- [ ] **Task C.5:** Launch. (*Owner: Cypher*)
