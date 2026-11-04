# serqet eval core

Offline benchmark package for SERQET. Run it from this directory:

```bash
uv sync --frozen --all-groups
uv run ruff check .
uv run mypy serqet
uv run pytest -q
uv run serqet verify --offline
```

The repository root README describes the full project. This package does not call a model API unless `serqet run-models` is invoked without `--dry-run`, a provider key is already in the environment, and `--cost-cap-usd` is greater than zero.
