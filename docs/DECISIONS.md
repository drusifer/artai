# artai — Decision Log

MADR-style records. Decided by Morpheus (or the owner where noted), recorded by Oracle.

---

## ADR-0001: One Python package, porting recard's Node runner
* **Status**: Accepted — 2026-10-20 (owner decision)
* **Context**: Two implementations exist: recard `tools/imagegen` (Node) and GlobalHeadsOrTails `tools/art_generator.py` (Python). Both already depend on Python + Pillow for image work.
* **Options**: (a) Python, port the Node runner/backends; (b) Node, port YAML/templates/autocrop/review and keep shelling out to Python for Pillow.
* **Decision**: (a). One runtime, no cross-language subprocess for image ops, and the newer GHOT code and its tests port directly.
* **Consequences**: + single toolchain, direct Pillow use. − recard's runner must be rewritten (~250 lines) and its tests re-expressed in pytest.

## ADR-0002: Two stages — generate masters, then pack
* **Status**: Accepted — 2026-10-20
* **Context**: recard keeps full-size masters and packs separately; GHOT generates and crops in one step, discarding the original.
* **Decision**: Keep masters in `work_dir/masters` and pack separately.
* **Consequences**: + re-packing at a new size/fit costs no quota; resume checks masters, which are what generation produces. − operators run two commands (`generate`, `pack`); `status` reports both counts to avoid confusion.

## ADR-0003: Providers through the standard library only
* **Status**: Accepted — 2026-10-20
* **Context**: The Gemini provider was a raw `fetch` in Node; codex/agy are CLIs.
* **Options**: vendor SDK (`google-genai`) vs `urllib.request`.
* **Decision**: `subprocess` for CLIs and `urllib.request` for Gemini; endpoint/CLI paths overridable by env for testing.
* **Consequences**: + no new dependencies, no SDK version churn, easy to stub. − we own request/response parsing; API changes need code edits.

## ADR-0004: Per-item claim files instead of production lanes
* **Status**: Accepted — 2026-10-20
* **Context**: GHOT ran 16 workers across detached "lanes" (`sticker_production.py`) plus per-image locks. Lane supervision was project-specific.
* **Decision**: Exclusive `claims/<id>.lock` holding `{pid, start_time, host}`, created by `os.link` from a fully written temp file (never seen half-written); taking over a dead owner's claim happens under `fcntl.flock` (see docs/LESSONS.md); any number of `artai generate` processes may run; dead owners' claims are taken over automatically.
* **Consequences**: + parallel runs are safe without a supervisor. − no built-in detach/monitor; operators use `nohup`/tmux. Lane management stays out of scope.

## ADR-0005: Safe defaults
* **Status**: Accepted — 2026-10-20
* **Decision**: codex runs with `--sandbox workspace-write`, never `--dangerously-bypass-approvals-and-sandbox` (GHOT's later "codex-safe" decision); `--backend` is required (no default), so a missing flag neither spends quota nor writes placeholder art; mock masters are tagged and never count as finished art for real runs or `verify` (Smith Gate 2); manifest commands run without a shell; agy permission bypass only for single-item opt-in.
* **Consequences**: + no accidental spend, no shell injection via prompts. − recard's `art-gen` must add `--backend codex` when it migrates.
