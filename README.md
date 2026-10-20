# artai

Manifest-driven, resumable AI artwork generation: a list of prompts in, reviewed, web-ready
images out. Consolidates the art tooling previously living in `recard` (`tools/imagegen`) and
`GlobalHeadsOrTails` (`tools/art_generator.py`).

## Setup

```sh
make install
make test
```

`make help` lists every target. How the project is built, tested and changed: `docs/SDLC.md`.

## Use

```sh
.venv/bin/artai prompts my_set.yaml                 # check prompts first
.venv/bin/artai generate my_set.yaml --backend codex
.venv/bin/artai pack my_set.yaml && .venv/bin/artai review my_set.yaml && .venv/bin/artai verify my_set.yaml
```

Full reference: `docs/USAGE.md`. Switching recard / GlobalHeadsOrTails over: `docs/MIGRATION.md`.
Design: `docs/ARCH.md`, `docs/DECISIONS.md`.
