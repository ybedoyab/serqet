#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cd packages/eval
uv sync --frozen --all-groups
uv run ruff check .
uv run mypy serqet
uv run pytest -q
uv run serqet verify --offline
python ../../scripts/check_secrets.py
