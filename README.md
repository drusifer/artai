# artai

Manifest-driven, resumable AI artwork generation: a list of prompts in, reviewed, web-ready
images out. Consolidates the art tooling previously living in `recard` (`tools/imagegen`) and
`GlobalHeadsOrTails` (`tools/art_generator.py`).

## Setup (developing artai)

```sh
make install
make test
```

`make help` lists every target. How the project is built, tested and changed: `docs/SDLC.md`.

## Install (using artai elsewhere)

artai is pip-installable (not published to PyPI). Into any Python ≥ 3.11 virtualenv:

```sh
pip install /path/to/artai        # puts the `artai` command on that venv's PATH
```

## Used by

- **recard** — `make art-install`, `art-gen`, `art`, `art-review`, `art-verify` (card art).
- **GlobalHeadsOrTails** — `make install-art`, `art-status`, `art-generate`, `art-pack`, `art-review`, `art-verify` (stickers).

Both expect this repo checked out beside them (`../artai`, override with `ARTAI_SRC=`) and
pip-install it editable into their own environment.

## Use

```sh
artai prompts my_set.yaml                 # check prompts first
artai generate my_set.yaml --backend codex
artai pack my_set.yaml && artai review my_set.yaml && artai verify my_set.yaml
```

(From this checkout, `artai` is `.venv/bin/artai`.)

## Documentation

| Document | What it covers |
|---|---|
| [docs/USAGE.md](docs/USAGE.md) | Every command, option, environment variable and manifest field |
| [docs/ARCH.md](docs/ARCH.md) | Architecture: components, flows, failure modes |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Decision records ADR-0001 … ADR-0006 |
| [docs/SDLC.md](docs/SDLC.md) | Toolchain, make targets, quality gates, change management |
| [docs/LESSONS.md](docs/LESSONS.md) | Engineering lessons |
| [docs/BACKLOG.md](docs/BACKLOG.md) | What's next |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| [docs/sprints/](docs/sprints/) | Sprint 1 stories and UAT plan; Sprint 2 migration plan |
| [task.md](task.md) | Current sprint task board |
| [agents/](agents/) | Bob Protocol team: personas, state, chat ([index](agents/DOCUMENTATION_INDEX.md), [chat archive](agents/chat_archive/)) |
