# Evaluation runbook

## Offline, every time

```bash
cd packages/eval
uv sync --frozen --all-groups
uv run serqet verify --offline
```

Exit code `0` means the four controls still separate. Exit code `1` means a task or the grader regressed. Fix that before trusting any model number.

## Dry run of the model path

```bash
uv run serqet run-models --model openrouter/some-model --trials 3 --cost-cap-usd 0 --dry-run
```

This writes prompt hashes only and does not call a provider.

## A real pilot

Do this only after a key is already in the environment and you have chosen a number you are willing to spend.

```bash
# shell environment, not a file you commit
export OPENROUTER_API_KEY=...
uv run serqet run-models --model <provider/model-id> --trials 3 --cost-cap-usd <explicit-cap>
```

As shipped, a positive cap with a visible key still returns `NOT_MEASURED` and does not start a sweep. The HTTP helper `live_chat` exists behind that gate and refuses a zero cap. Turning on a sweep means reviewing this runbook, recording the model id and the UTC time, and storing redacted traces under `artifacts/measured/<run_id>/{metadata.json,raw_events.jsonl,score.json}` with `"kind": "measured"`. Then:

```bash
uv run serqet report --input artifacts/measured --output artifacts/summary.json
```

Provider errors stay out of the agent-failure denominator. Do not describe an older model as frontier without evidence. Do not paste keys into the chat log, the ZIP, or the dashboard.
