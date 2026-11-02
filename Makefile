# artai — the Makefile is the front door; see docs/SDLC.md.
PYTHON := .venv/bin/python
NEED_VENV = @test -x $(PYTHON) || { echo "No .venv - run 'make install' first"; exit 1; }

.DEFAULT_GOAL := help
.PHONY: help install test lint format build release-setup release run clean distclean

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
	$(PYTHON) -m ruff format src tests
	$(PYTHON) -m ruff check --fix src tests

build: ## Build sdist + wheel into dist/ and check them (twine)
	$(NEED_VENV)
	rm -rf dist
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

# Publish to public PyPI via GitHub trusted publishing: creating a GitHub Release
# triggers .github/workflows/release.yml (OIDC; no token). Needs `gh` authenticated.
VERSION := $(shell sed -n 's/^__version__ = "\(.*\)"/\1/p' src/artai/__init__.py)
PKG_VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)

# One-time setup is manual (neither PyPI nor the GitHub environment is scripted); this
# target only prints the steps with this repo's values.
GH_REPO := $(shell git remote get-url origin | sed -E 's#.*github.com[:/](.*)\.git#\1#')
PYPI_NAME := artai

release-setup: ## Print the one-time manual steps for publishing to PyPI
	@echo "1. Check the PyPI name is free:  https://pypi.org/project/$(PYPI_NAME)/  (404 = free)"
	@echo "2. GitHub environment:  https://github.com/$(GH_REPO)/settings/environments"
	@echo "     New environment named: pypi  (optional: add yourself as required reviewer)"
	@echo "3. PyPI trusted publisher:  https://pypi.org/manage/account/publishing/  (or your org's page)"
	@echo "     Add a pending publisher (GitHub):"
	@echo "       PyPI project name: $(PYPI_NAME)"
	@echo "       Owner/repo:        $(GH_REPO)"
	@echo "       Workflow:          release.yml"
	@echo "       Environment:       pypi"
	@echo "4. Push main, then run: make release"

release: lint test ## Tag v<version> (if missing), push, create the GitHub Release that publishes to PyPI
	@test -n "$(VERSION)" || { echo "cannot read version"; exit 1; }
	@test "$(VERSION)" = "$(PKG_VERSION)" || { echo "version mismatch: __init__ $(VERSION) vs pyproject $(PKG_VERSION)"; exit 1; }
	@test "$$(git rev-parse --abbrev-ref HEAD)" = main || { echo "release must run from main"; exit 1; }
	@git diff --quiet HEAD -- pyproject.toml src || { echo "uncommitted changes in package files"; exit 1; }
	@git fetch -q origin main && test "$$(git rev-parse HEAD)" = "$$(git rev-parse origin/main)" || { echo "HEAD must match origin/main (push first)"; exit 1; }
	@git rev-parse -q --verify refs/tags/v$(VERSION) >/dev/null || git tag -a v$(VERSION) -m "artai $(VERSION)"
	git push origin v$(VERSION)
	@gh release view v$(VERSION) >/dev/null 2>&1 && { echo "release v$(VERSION) already exists"; exit 1; } || true
	gh release create v$(VERSION) --generate-notes --title "artai $(VERSION)"

run: ## Run the artai CLI (ARGS="...")
	$(NEED_VENV)
	.venv/bin/artai $(ARGS)

clean: ## Remove caches and build outputs (keeps .venv)
	rm -rf dist src/*.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +

distclean: clean ## clean + remove .venv
	rm -rf .venv
