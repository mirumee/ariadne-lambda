# Development tasks (requires uv: https://docs.astral.sh/uv/ and just: https://github.com/casey/just)
# Sync env: uv sync --all-extras

lint:
    uv run ruff format --check ariadne_lambda tests
    uv run ruff check ariadne_lambda tests
    uv run ty check

fmt:
    uv run ruff format ariadne_lambda tests
    uv run ruff check --fix ariadne_lambda tests

test:
    uv run pytest

test-cov:
    uv run pytest --cov --cov-report=term-missing

check: fmt test test-cov
    uv run ty check

changelog-preview:
    uv run git-cliff --unreleased --strip all

changelog-update:
    uv run git-cliff --unreleased -o CHANGELOG.md

release-notes:
    uv run git-cliff --latest --strip all
