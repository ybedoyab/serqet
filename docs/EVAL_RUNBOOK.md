# Evaluation runbook

## Offline, every time

Run from the repository root. `artifacts/` is that root, not `packages/eval/artifacts`.

```bash
uv sync --project packages/eval --frozen --all-groups
uv run --project packages/eval serqet verify --offline
```

Exit code `0` means the four controls still separate. Exit code `1` means a task or the grader regressed. Fix that before trusting any model number. `verify --offline` refreshes controls and simulated demos. It keeps model rows only when the files under `artifacts/measured` pass integrity checks. It does not turn a `kind: measured` flag into a result.

To check the published trials without rewriting them and without an API key:

```bash
uv run --project packages/eval serqet audit
```

`audit` must report 31 accepted trials and cost USD 0.547108. It does not call a provider.

## Dry run

```bash
uv run --project packages/eval serqet run-models --model openrouter/some-model --trials 1 --cost-cap-usd 0 --dry-run
```

This writes prompt hashes only and does not call a provider.

## Provider and budget

`--provider openrouter` reads `OPENROUTER_API_KEY` and posts to `https://openrouter.ai/api/v1/chat/completions`. `--provider openai` reads `OPENAI_API_KEY` and posts to `https://api.openai.com/v1/chat/completions`. An OpenAI key is not sent to OpenRouter.

A live run also needs all of the following, or the command exits `2` before any socket:

- `--cost-cap-usd` greater than 0
- `--input-usd-per-mtok` and `--output-usd-per-mtok`
- the credential for the selected provider

Before each request the harness estimates a worst-case cost from the message size and `--max-output-tokens`. If the prices are missing or the remaining cap cannot cover that estimate, it does not send the request. Reported `usage.cost` is stored when the provider sends it; otherwise token counts are priced with the rates you passed. The cap is not a billing guarantee. The metadata field `cost_is_billing_guarantee` is false.

Defaults: `--max-turns 8`, `--max-output-tokens 700`, one retry on 408, 409, 429, and 5xx. Those HTTP failures are infrastructure, not model failures.

## Staged protocol

The 4 November 2026 run used a shared ledger at `artifacts/budget/ledger.json` with a harness ceiling of USD 4.50 inside a provider key limit of USD 5. Separate `--cost-cap-usd` values cannot each spend USD 5. That ledger is not a billing guarantee. The completed matrix is `docs/FRONTIER_MODEL_FINDINGS.md`. The templates below are the commands that were used, with the caps passed to each process.

### Stage A — pilot

Two families, including one revocation family. Two distinct current models. One trial. One mode first (`shadow` or `enforced`, not both) so the bill stays small. Read the transcripts before widening the sample.

From the repository root, after the key is in the process environment and a numeric cap has been approved. The harness does not read `.env` by itself. `--measured-dir` is relative to the repository root.

```bash
uv run --project packages/eval serqet run-models \
  --provider openrouter \
  --model <provider/model-id> \
  --scenarios consent-disclosure-holds,consent-revoked-before-commit,approval-holds,approval-withdrawn \
  --mode shadow \
  --trials 1 \
  --max-turns 8 \
  --max-output-tokens 700 \
  --cost-cap-usd <cap> \
  --input-usd-per-mtok <rate> \
  --output-usd-per-mtok <rate> \
  --measured-dir artifacts/measured/stage-a/<model-slug>
```

### Stage B — full benchmark

Only after Stage A transcripts look faithful: all 10 tasks, three trials when the cap allows, then the other gateway mode. Compare attempts, effects, authorized completions, escalations, false refusals, and false success claims. Shadow and enforced stay separate columns.

### Stage C — replication

Re-run failures that look like authority mistakes. Keep provider errors out of that comparison. If a surprising fail disagrees with the policy or the event order, fix the harness before quoting the score.

## Publishing

A trial directory needs `metadata.json`, `transcript.json`, `events.json`, `score.json`, and `responses.json`. The validator replays the events, checks the model id and timestamps, and rejects incomplete cost or provider failures.

```bash
uv run --project packages/eval serqet report --input artifacts/measured/stage-a --output artifacts/summary.json
```

`report` reads `--input` relative to the current directory. From `packages/eval` that path would be `../../artifacts/measured/stage-a`. The command above assumes the repository root.

Exit `0` with `MEASURED` means at least one trial passed that check. Exit `2` means nothing publishable was found. Keys, `Authorization` headers, and bearer tokens are not written. If a response still contains a credential marker, validation fails.
