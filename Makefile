# artai — the Makefile is the front door; see docs/SDLC.md.
PYTHON := .venv/bin/python
NEED_VENV = @test -x $(PYTHON) || { echo "No .venv - run 'make install' first"; exit 1; }

.DEFAULT_GOAL := help
.PHONY: help install test lint format build run clean distclean

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

$(PYTHON):
	python3 -m venv .venv

install: $(PYTHON) ## Create .venv and install artai with dev dependencies (idempotent)
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -e ".[dev]"

test: ## Run the test suite (ARGS="-k name")
	$(NEED_VENV)
	$(PYTHON) -m pytest $(ARGS)

lint: ## Static checks with ruff (no changes)
	$(NEED_VENV)
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests

format: ## Rewrite files to project style
	$(NEED_VENV)
	$(PYTHON) -m ruff check --fix src tests
	$(PYTHON) -m ruff format src tests

run: ## Run the artai CLI (ARGS="...")
	$(NEED_VENV)
	.venv/bin/artai $(ARGS)

clean: ## Remove caches and build outputs (keeps .venv)
	rm -rf dist src/*.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +

distclean: clean ## clean + remove .venv
	rm -rf .venv
