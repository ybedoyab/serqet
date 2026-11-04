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

## Three ways to check, and which ones spend money

Offline controls and the existing measured artifacts do not need an API key.

```bash
uv run --project packages/eval serqet audit
```

Run that from the repository root after `uv sync --project packages/eval --frozen --all-groups`. `audit` replays the four reference controls, validates every accepted trial, recomputes the published cost sum, and checks the evidence rollup. It does not call a provider and it does not rewrite `artifacts/measured`. Exit 1 means the frozen bytes or the control separation no longer match.

`serqet verify --offline` answers the same control question and also rewrites `artifacts/summary.json`, `artifacts/demo/`, and `apps/web/data/benchmarks.json`. Use it when you intend to refresh the dashboard bundle. Use `audit` when you must leave the measured files untouched.

A new model run is optional and is not required to confirm the published scores. `run-models` without a positive `--cost-cap-usd`, a provider key, and token prices exits `2` before any socket. A live rerun spends money and must be stored as a new run, not as a rewrite of the 4 November files.

## Approximate cost and time

Offline `audit` is seconds on a laptop and costs nothing. The published trials already exist. Do not buy credits to reproduce them.

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
