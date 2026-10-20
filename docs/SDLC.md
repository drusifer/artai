# artai — SDLC

How this project is built, tested, changed and released — the source of truth for change
management across the whole project. **Owned by Tank**; to change anything here,
ask `@Tank *devops sdlc <what and why>` — the mechanism and this document change together.

## 1. Toolchain

| | Python |
|---|---|
| Runtime version | ≥ 3.11 — `requires-python` in `pyproject.toml` (verified on 3.13.5) |
| Manifest | `pyproject.toml` (PEP 621 `[project]`; pytest and ruff config in `[tool.*]`) |
| Lockfile | None — plain pip has none; lower bounds are pinned in the manifest |
| Package manager | stdlib `venv` + `pip` |
| Local environment | `.venv/` (gitignored, `include-system-site-packages = false`) |
| Layout | `src/artai/` package, `tests/` (pytest) |

Other required tools: GNU `make`, a system `python3` with the `venv` module (to create `.venv`),
and `bobp` (agents run every target through `bobp make`). Image-generation backends call
external tools/services (e.g. `codex`, `agy`, Gemini API) at run time only; they are **not**
needed to install or test — tests use an offline mock backend.

## 2. Setup

From a clean checkout:

```sh
make install     # creates .venv, then pip install -e ".[dev]"
make test        # should print "N passed"
```

`make run ARGS="--version"` printing `artai <version>` confirms the CLI entry point is installed.
Nothing is installed into the system Python. Never use `sudo pip` or `--break-system-packages`.

## 3. Make targets

The Makefile is the only entry point; recipes call `.venv/bin/python` and stop with
"run 'make install' first" if `.venv` is missing. Agents invoke them as `bobp make <target>`
(output captured in `build/build.out`).

| Target | Runs | Notes |
|---|---|---|
| `install` | `python3 -m venv .venv` (if absent), `pip install -e ".[dev]"` | idempotent; the only target that uses the network |
| `test` | `.venv/bin/python -m pytest` | `ARGS="-k name"` passes through |
| `lint` | `ruff check src tests` + `ruff format --check src tests` | changes nothing |
| `format` | `ruff format`, then `ruff check --fix` | rewrites files; formats first so an unfixable lint error cannot stop formatting (changed Sprint 1) |
| `run` | `.venv/bin/artai $(ARGS)` | |
| `clean` | removes `dist/`, `*.egg-info`, pytest/ruff caches, `__pycache__` | keeps `.venv` |
| `distclean` | `clean` + removes `.venv/` | used for the from-clean check |
| `help` | lists targets (default goal) | |

Standard targets deliberately absent: `build` — nothing is published; consumers install from a
checkout with pip (section 7), which builds the wheel itself. Add `build` when a release channel
(PyPI, wheel artifact) is chosen.

## 4. Dependencies

- **Add a runtime dependency:** add it to `[project] dependencies` with a lower bound, then
  `make install`.
- **Add a dev/test tool:** add it to `[project.optional-dependencies] dev`, then `make install`.
- **Optional features:** none yet. A backend needing a heavy SDK should become an extra
  (e.g. `gemini = [...]`) included by `dev`, so the core install stays small.
- **Upgrade / remove:** edit the bound or delete the line, then `make distclean && make install`.
- **Commit afterwards:** `pyproject.toml`.
- **Who:** Neo adds and bumps dependencies. A new package manager, language or Python version
  is a mechanism change — Tank's.
- `requirements.txt`: absent — never the source of truth.

## 5. Quality gates

| Gate | Target | Required before |
|---|---|---|
| Tests | `make test` | every handoff to Trin; every phase commit; sprint close |
| Lint + format check | `make lint` | every phase commit; sprint close |

No secret scanner is configured. Backends read credentials (e.g. `GEMINI_API_KEY`) from the
environment only; reviewers check that no key is written to code, manifests, logs or commits.

## 6. Change management

This document is the project's source of truth for how a change gets from request to done.
Where another document, skill or habit disagrees with it, this one wins — and the disagreement
is reported to Tank so one of them gets fixed.

### Change classes

| Class | Examples | Proposed by | Approved by | Must pass | Recorded in |
|---|---|---|---|---|---|
| Routine | feature, fix, refactor, docs, adding a dependency via section 4 | User request → Cypher story | Morpheus phase review | section 5 gates | `task.md`, phase commit |
| Mechanism | toolchain, manifest layout, make targets, gates, CI, this document | anyone, via `@Tank *devops sdlc` | Tank + user | from-clean rebuild + section 5 | this file, `agents/CHAT.md` |
| Release | version bump, tag | Cypher at sprint launch | user | section 5 gates + Tank `*devops sdlc-check` | `CHANGELOG.md`, git tag |
| Emergency | hotfix outside a sprint | user | user (may be after the fact) | `make test` at minimum | commit message, reviewed at next sprint close |

### Flow

1. **Request** — the user asks; work is planned as a sprint (`*plan sprint`) or a Bloop loop
   (`*fix`, `*impl`, ...) and tracked in root `task.md`.
2. **Branch** — work directly on `main`. No sprint branches.
3. **Implement** — through `make` targets only; tests accompany behaviour changes (TDD).
4. **Gate** — `make test` and `make lint` pass locally before handoff.
5. **Review** — Trin runs UAT for the phase, then Morpheus reviews the code; Morpheus's
   pass in `agents/CHAT.md` is the approval.
6. **Integrate** — after Morpheus approves a phase, the active persona commits that phase to
   `main` locally. Message: `<type>(<scope>): <summary>` (types: feat, fix, refactor, docs,
   test, chore, build), ending with the attribution trailer the harness supplies.
7. **Record** — tick the phase in `task.md`; post the commit hash to `agents/CHAT.md`.

### Rules

- Agents commit locally, once per approved phase. **Agents never push**; the user pushes.
- Never commit: secrets/API keys, `.venv/`, `build/` (generated masters, logs, `build.out`),
  `.mcp.json`, `.via/`.
- **Rollback:** `git revert <phase commit>` — phases are one commit each, so reverting one is
  a single command; then `make test`.
- **Changing this document:** only Tank edits it; every edit updates the Last verified line.

## 7. Versioning and release

- **Version lives in:** `[project] version` in `pyproject.toml`, mirrored by
  `artai.__version__` in `src/artai/__init__.py` (both must change together).
- **Bumped:** by Cypher at sprint launch, with user approval; semver (minor for features).
- **CLI entry points:** `[project.scripts] artai = "artai.cli:main"` — installed to
  `.venv/bin/artai` by `make install`.
- **Artifact:** None published (no PyPI, no wheel kept). The package is pip-installable from
  source via the `setuptools` backend in `pyproject.toml`:
  - `pip install /path/to/artai` — from a checkout, into any Python ≥ 3.11 venv; installs only
    runtime dependencies (Pillow, PyYAML) and puts `artai` on that venv's PATH.
  - `pip install git+<repo-url>@<tag-or-commit>` — once the repo is pushed; consumers should pin
    a tag or commit, not a branch.
  - Calling `../artai/.venv/bin/artai` by path also works.
  Consumers (Sprint 2, ADR-0006): recard `make art-install` → its `.venv`; GlobalHeadsOrTails
  `make install-art` → `.venv-art`; both `pip install -e ../artai` (override `ARTAI_SRC=`).
  An artai change therefore reaches both immediately — run their `art-verify` after CLI changes.
  Verified: fresh venv, `pip install` at f9a85ac → `artai 0.1.0`, deps pillow 13.0.0, PyYAML 6.0.3.

## 8. CI / deploy

None — everything runs locally. If CI is added it must run `make install && make test && make lint`.

## 9. Known deviations

- No lockfile (plain pip). Reproducibility relies on lower bounds; acceptable for a local tool
  with two runtime dependencies. Close by switching to `uv` + `uv.lock` (mechanism change) if
  versions drift between machines.
- `build/` is shared by `bobp make` output capture and generated-art scratch; both are
  machine-local and gitignored.
- POSIX only (Linux verified): claim takeover uses `fcntl.flock`, provider timeouts kill process
  groups, and liveness reads `/proc` (falls back to `os.kill` elsewhere). Both consumers run on
  Linux; Windows support would need a different lock (ADR-0004).
- `tests/fixtures/ghot` and `tests/fixtures/recard` are copies of the consumer projects' inputs
  (2026-10-20). They are parity evidence, not live links; refresh them when those inputs change.

## 10. Conformance check

Run by Tank at sprint close (`*devops sdlc-check`):

1. `bobp make distclean && bobp make install && bobp make test && bobp make lint` all exit 0.
2. Every third-party import under `src/` is declared in `pyproject.toml`: check with
   `grep -rhoE '^(import|from) [a-zA-Z_]+' src | sort -u` against `[project] dependencies`.
   An undeclared import fails; Neo fixes.
3. `.venv/pyvenv.cfg` says `include-system-site-packages = false`.
4. Every target in section 3 exists in `make help` and does what the table says; any new target
   is listed here or removed.
5. No doc or script tells people to *develop or test* artai with bare `python3`/`pip`/`pytest`
   instead of `make`: `grep -rnE '(^|\s)(pip|pytest) ' README.md docs | grep -v 'pip install /path/to/artai\|pip install git+'`
   shows only this file's lines. (`pip install /path/to/artai` and `pip install git+…` are the
   section 7 consumer install routes and are allowed.)
6. `.venv/`, `build/`, `*.egg-info/` are gitignored (`git check-ignore` succeeds for each);
   `requires-python` unchanged or deliberately bumped.
7. This sprint's commits: one per approved phase, on `main`, conventional message, nothing
   pushed by an agent (`git status -sb` shows no upstream change made by agents).
8. `pyproject.toml` version equals `artai.__version__`.
9. `git grep -nE 'AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,}'` finds no credential.
10. `pip install .` into a throwaway venv succeeds and `artai --version` matches the
    `pyproject.toml` version (proves the section 7 install route still works).

---
*Last verified: 2026-10-20 against 52085c0 (Sprint 2 close) by Tank — lint, secrets, no code change since
50406ec (136+2 tests then); consumers: GlobalHeadsOrTails `.venv-art` rebuilt from clean → art-verify 36/36;
recard art-verify 132/132.*
