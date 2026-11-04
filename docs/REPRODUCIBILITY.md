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

## Environment recorded for the measured run

- Date: 4 November 2026
- Runner commit before the write-up: `97c1044d1f93ae26156d810964aa832de3c83401`
- Measurement: `MEASURED`, 31 accepted trials, 0 rejected
- Models: `openai/gpt-6-sol`, `anthropic/claude-sonnet-5.5`, provider `openrouter`
- Request settings: temperature 0, max turns 8, max output tokens 700, timeout 90 seconds
- Prices used: USD 2 per million input tokens, USD 10 per million output tokens
- Harness sum of provider-reported `usage.cost`: USD 0.547108
- OpenRouter key usage after the runs: USD 0.5471084 of a USD 5 lifetime key limit
- Raw trials: `artifacts/measured/`
- The shared harness ledger ceiling was USD 4.50. It is local, gitignored, and is not a billing guarantee

## Environment recorded for the offline controls

- Date: 4 November 2026
- OS: Windows, with CI on Ubuntu
- Controls are unchanged: oracle 10/10, always-refuse 5/10, reckless 5/10, cached authority 8/10
