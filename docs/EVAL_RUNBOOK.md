# Evaluation runbook

## Offline, every time

```bash
cd packages/eval
uv sync --frozen --all-groups
uv run serqet verify --offline
```

Exit code `0` means the four controls still separate. Exit code `1` means a task or the grader regressed. Fix that before trusting any model number. `verify --offline` refreshes controls and simulated demos. It keeps model rows only when the files under `artifacts/measured` pass integrity checks. It does not turn a `kind: measured` flag into a result.

## Dry run

```bash
uv run serqet run-models --model openrouter/some-model --trials 1 --cost-cap-usd 0 --dry-run
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

No stage below was run against a paid provider in the harness commit. Do not start one without choosing a numeric cap you are willing to spend.

### Stage A — pilot

Two families, including one revocation family. Two distinct current models. One trial. One mode first (`shadow` or `enforced`, not both) so the bill stays small. Read the transcripts before widening the sample.

```bash
uv run serqet run-models \
  --provider openrouter \
  --model <provider/model-id> \
  --scenarios consent-revoked-before-commit,consent-disclosure-holds,approval-withdrawn,approval-holds \
  --mode shadow \
  --trials 1 \
  --cost-cap-usd <cap> \
  --input-usd-per-mtok <rate> \
  --output-usd-per-mtok <rate>
```

### Stage B — full benchmark

Only after Stage A transcripts look faithful: all 10 tasks, three trials when the cap allows, then the other gateway mode. Compare attempts, effects, authorized completions, escalations, false refusals, and false success claims. Shadow and enforced stay separate columns.

### Stage C — replication

Re-run failures that look like authority mistakes. Keep provider errors out of that comparison. If a surprising fail disagrees with the policy or the event order, fix the harness before quoting the score.

## Publishing

A trial directory needs `metadata.json`, `transcript.json`, `events.json`, `score.json`, and `responses.json`. The validator replays the events, checks the model id and timestamps, and rejects incomplete cost or provider failures.

```bash
uv run serqet report --input artifacts/measured --output artifacts/summary.json
```

Exit `0` with `MEASURED` means at least one trial passed that check. Exit `2` means nothing publishable was found. Keys, `Authorization` headers, and bearer tokens are not written. If a response still contains a credential marker, validation fails.
