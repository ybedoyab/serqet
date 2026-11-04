# Reproducibility

## Pinned runtime

- Python `>=3.12`. This workspace used CPython 3.12.3 and uv 0.12.5.
- Dependencies are locked in `packages/eval/uv.lock`.
- The web lockfile is `apps/web/package-lock.json` after `npm install`.
- Dataset version `serqet-2026-11-04.2`. `serqet verify` records `dataset_hash` over the scenario JSON bytes.

## Commands

From `packages/eval`:

```bash
uv sync --frozen --all-groups
uv run ruff check .
uv run mypy serqet
uv run pytest -q
uv run serqet verify --offline
```

`verify --offline` rewrites `artifacts/summary.json`, `artifacts/demo/*.json`, and `apps/web/data/benchmarks.json`. Two control runs in the test suite compare canonical score JSON and require equality. Scores do not include wall-clock timestamps.

## Offline boundary

`verify`, `baseline`, `scenarios list`, and `run-models --dry-run` do not call a model provider. A live `run-models` returns exit code 2, without opening a socket, when the cost cap is `0`, the selected provider's key is unset, or the per-million token prices are omitted. `OPENAI_API_KEY` is not sent to OpenRouter. HTTP errors stay infrastructure failures and cannot set `MEASURED` by themselves.

## Approximate cost and time

Offline verification is a few seconds on a laptop and costs nothing. A future model pilot is unbounded until you pass a positive cap; the default is zero. Do not expect a model leaderboard from this commit.

## Environment recorded for the offline run

- Date: 4 November 2026
- Measurement: `NOT_MEASURED`
- OS: Windows, with CI intended on Ubuntu
- No model id, temperature, or token count, because no model ran
