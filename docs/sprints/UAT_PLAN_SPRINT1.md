# Sprint 1 Acceptance Test Plan (UAT): One art tool for every project

> Note (Sprint 2): `docs/MIGRATION.md` and `agents/oracle/art_tooling_survey.md`, referenced below, were deleted once the migration landed; see git history.

*   **Sprint**: `SPRINT_1`
*   **Author**: Trin (*qa)
*   **Date**: 2026-10-20
*   **Branch**: `main`
*   **Status**: Passed

---

## 1. Scope of Acceptance Testing

* **User Stories Covered:** STORY-ART-1 … STORY-ART-7 (`docs/sprints/USER_STORIES_SPRINT1.md`).
* **In-Scope Workflows:** describe/preview a set; generate (resume, quota, parallel, concurrent
  processes, Ctrl-C); providers via stand-ins; pack; review; verify; regenerate; unlock; run both
  projects' inputs end to end; docs.
* **Out-of-Scope:** live calls to codex/agy/Gemini (Story Open Question 1 — owner's decision;
  codex and agy are installed on this host, so a one-image sample is possible on request);
  changing recard or GlobalHeadsOrTails.

## 2. Preconditions & Test Environment Setup

* **Environment:** Raspberry Pi OS, Python 3.13.5, `.venv` via `bobp make install`; Chromium for
  contact-sheet screenshots.
* **Fixtures & Test Data:** `tests/fixtures/ghot/` (4 manifests + data, expected prompts captured
  from `tools/art_generator.py --export-prompts`), `tests/fixtures/recard/` (12-line TSV and
  6-entry JSON from `genArtJobs.mjs`). Provider stand-in: `tests/helpers/fake_cli.py`
  (behaviour set by `FAKE_MODE`: ok, quota, fail, sleep, nothing, scratch).
* **Environment Verification Command:**
  ```bash
  bobp make install && bobp make test     # 136 passed
  ```

Each case was run from an empty scratch directory with `A=.venv/bin/artai`. Paths below are
shortened to `./`. Automated coverage for each AC is named in brackets.

## 3. Scenario-Driven Acceptance Test Cases

### UAT-ART-1-01: Preview a GHOT set before spending quota
* **User Story:** STORY-ART-1 (AC1, AC3, AC4, AC7) · **Persona:** art operator
* **Steps:** `$A prompts --json fantasy-heroes/manifest.yaml`; `$A status rangers-history/champions.yaml`; `$A status --work W --out O rtg_jobs.json`
* **Expected:** 12 prompts identical to GHOT's export; status lists 82 items, 8 missing ids then `... and 74 more`; overrides resolve to `./W/masters`, `./O`. Exit 0, nothing written.
* **Result:** [x] Pass
  ```text
  identical 12
  items:        82 … missing:      82 / nyr-8446641 … ... and 74 more
  masters:      0   (./W/masters)   packed:       0   (./O)
  ```
  [test_prompts::test_parity_with_ghot_export_prompts — 273/273 across 4 manifests; test_cli_phase1]

### UAT-ART-1-02: Bad manifest and unknown placeholder
* **User Story:** STORY-ART-1 (AC2, AC5, AC6)
* **Steps:** TSV with a line lacking a tab; YAML with `{nope}`; `--style` on a TSV.
* **Expected:** `artai: bad.tsv: line 2: …`, exit 1, directory unchanged; warning names item and placeholder, prompt keeps `{nope}`; style appended.
* **Result:** [x] Pass
  ```text
  artai: bad.tsv: line 2: expected <id><TAB><prompt>, got "broken"     (exit 1; only bad.tsv present)
  warning: a: no value for placeholder {nope}
  a	x {nope}
  ```
  [test_manifest::test_invalid_manifests_name_file_and_problem ×10]

### UAT-ART-2-01: Resumable generation, corrupt master, logs
* **User Story:** STORY-ART-2 (AC1, AC2, AC8)
* **Steps:** `generate twelve-clans --backend mock --parallel 4`; overwrite one master with junk; run again.
* **Expected:** 36 generated; second run regenerates only the junk one; per-attempt log lines.
* **Result:** [x] Pass
  ```text
  artai — 36 generated, 0 already present, 0 busy elsewhere, 0 failed
  ok    [21/36] dawn-oath-1
  artai — 1 generated, 35 already present …
  === attempt 1 · backend mock · 2026-10-20T18:27:58+00:00 ===
  ```

### UAT-ART-2-02: Two processes, one work directory
* **User Story:** STORY-ART-2 (AC6, AC7)
* **Steps:** two `generate rangers-history --parallel 4` processes at once, one with `--reverse`.
* **Expected:** every item generated exactly once; claimed items reported busy; no claim left behind.
* **Result:** [x] Pass — 143 masters, 0 ids generated twice, 0 `.lock` files left.
  [test_runner::test_two_processes_never_generate_the_same_item]

### UAT-ART-2-03: Quota, failure, interruption, bad options
* **User Story:** STORY-ART-2 (AC3, AC4, AC5) · STORY-ART-3 (AC6)
* **Steps:** fake codex in quota mode on a 12-item TSV; `--parallel 9`; `--ids i1,zz`; SIGINT during a 60 s provider call.
* **Expected:** quota → stop, marker, advice, exit 2; bad options refused before writing; Ctrl-C exits 130 within seconds, no claims left.
* **Result:** [x] Pass
  ```text
  QUOTA [1/12] rtg-b-001
  ✖ provider quota exhausted — run stopped early (11 item(s) not started).
    Re-run the same command after the quota resets; finished images are skipped.   exit=2
  quota:        exhausted at 2026-10-20T18:31:53+00:00 …   (status)
  ```
  [test_cli_generate::test_parallel_bounds, test_unknown_ids_refused; test_providers::test_ctrl_c_stops_quickly_and_releases_claims]

### UAT-ART-3-01: Providers
* **User Story:** STORY-ART-2 (AC9), STORY-ART-3 (AC1–5)
* **Steps:** fake codex on fantasy-heroes after mock; argv inspected; command backend with an injection prompt; agy scratch + yolo; Gemini against a stub server.
* **Expected:** codex argv `exec --sandbox workspace-write --skip-git-repo-check`, no bypass flags; 12 placeholders replaced by real art; injection runs nothing; agy newest scratch file claimed, yolo refused for >1 item; Gemini key only in header, 429 → quota, non-PNG → failure.
* **Result:** [x] Pass
  ```text
  ['exec', '--sandbox', 'workspace-write', '--skip-git-repo-check']
  Generate a PNG image using your image generation tool — … Do not write code to draw it. Subject: …
  masters:      12   placeholders: 0
  ```
  [test_providers — 24 tests]

### UAT-ART-4-01: Pack both fit modes
* **User Story:** STORY-ART-4 (AC1–5)
* **Steps:** pack twelve-clans (autocrop); pack recard TSV with `--out assets/cards/rtg --quality 82`.
* **Expected:** 512×512 WebP for the YAML set; contain-fit for lists; `packed X/Y`; bad master skipped with old output kept.
* **Result:** [x] Pass — `(512, 512) WEBP`; `packed 12/12 → ./assets/cards/rtg`, all 512×512 (square masters).
  [test_pack — 1024×1536 → 341×512; autocrop centring; unopenable master]

### UAT-ART-5-01: Contact sheet and verify gate
* **User Story:** STORY-ART-5 (AC1–5)
* **Steps:** `review`, screenshot at 1280 px and 375 px; `verify` with missing, placeholder, duplicate and complete sets; `--ids` sample.
* **Expected:** readable page, missing/placeholder marked, no sideways scroll on a phone; verify exit 1 naming each problem, exit 0 only when complete; sample notice.
* **Result:** [x] Pass (after 2 fixes in phase 4: phone overflow; long lore moved into details)
  ```text
  ✖ crownless-court-2: no packed image                       (exit 1)
  ✖ hearthshield-compact-hero and brassburrow-guild-hero: identical images   (identical fake output caught)
  artai — 12/12 verified for set fantasy_heroes             (exit 0, distinct images)
  note: this result covers the selected sample only and cannot show the set is complete
  ```

### UAT-ART-6-01: Regenerate and unlock
* **User Story:** STORY-ART-6 (AC1–4)
* **Steps:** `regenerate --ids mosswhisper-circle-hero --backend codex`; `verify` before and after `pack`; `regenerate` without `--ids`; `unlock` a dead claim; (live-claim refusal in tests).
* **Expected:** master + WebP archived under `rejected/<UTC>/`, item regenerated, hint to pack; verify 11/12 until packed, then 12/12; no-ids refused; dead claim cleared.
* **Result:** [x] Pass
  ```text
  set aside 2 file(s) → ./build/artai/fantasy_heroes/rejected/2026-10-20T18-41-59Z
  next: artai pack …   (the regenerated items have no packed image yet)
  artai — 11/12 verified (exit 1) → after pack: 12/12 verified (exit 0)
  artai: regenerate needs --ids (which items to regenerate); it never acts on a whole set   (exit 1)
  cleared stale claim: dawn-oath-hero
  ```
  [test_regenerate_unlock — all-or-nothing refusal with a real live process]

### UAT-ART-7-01: Both projects end to end, and the docs
* **User Story:** STORY-ART-7 (AC1–4)
* **Steps:** `bobp make test ARGS="-k parity"`; check USAGE lists every command and MIGRATION every current make target; facts in MIGRATION checked against the source repos.
* **Expected:** 6 fixtures pass status → prompts → generate → pack → review → verify; docs complete.
* **Result:** [x] Pass — 6/6 parity tests; USAGE: all 8 commands; MIGRATION: `art-gen`, `art`, `art-status`, `art-generate`, `art-review`. One MIGRATION fact corrected (479 Rangers masters, 90 + 37 reusable — not 973).

## 4. Defects found and fixed during UAT

| Phase | Defect | Fix |
|---|---|---|
| 2 | Ctrl-C would wait for the provider's timeout (up to 10 min) | provider process groups killed on interrupt; exit 130 |
| 2 (review) | Two runs could both take over the same stale claim | takeover serialised with a directory lock |
| 3 | Quota message printed before the summary line when piped | flush stdout |
| 4 | Contact sheet scrolled sideways on phones; long lore swamped cards | responsive grid, wrapped path, long fields in details |
| 5 | Manifest `min_size` ignored by `generate` | manifest value is the default; `--min-size` overrides |
| close (Smith) | Usage errors (mistyped command/option) exited 2 = the quota code | argparse errors mapped to 1 (`50406ec`) |
| close (Smith) | `verify` gave no next step when only the pack was missing | "(master exists — run artai pack)" |

## 5. Sign-off

All 7 stories accepted against their criteria. Open item for the owner: one live sample per real
provider before the migration sprint (`docs/MIGRATION.md` checklist).
