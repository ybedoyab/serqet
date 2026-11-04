# Security

SERQET stores no real patient data and does not expose a write API. The dashboard is a static view of generated JSON.

## Handling secrets

- Do not commit `.env`. Commit `.env.example` with empty values only.
- `scripts/check_secrets.py` scans the tree for private-key blocks and common key prefixes (`sk-`, `sk-ant-`, `sk-or-`, `ghp_`, `github_pat_`, `AKIA`, `xai-`).
- Logs and the ZIP must not contain provider keys. The model client reads the key from the environment and does not print it.
- The default cost cap is `0`. `run-models` exits before any socket when the cap is `0` or the key is missing.

## Web

- No `dangerouslySetInnerHTML`.
- Response headers set a restrictive Content-Security-Policy, `nosniff`, `DENY` framing, and a locked-down Permissions-Policy.
- There is no public inference route. `/api/health` returns `{ok, service, commit}` only.

## Sandbox

- Tools cannot name a filesystem path or a URL to fetch.
- Maximum 24 tool calls per session.
- Untrusted note text cannot change `policy.py`.
- Agent-supplied audit prose is not stored as `AuditEvent`.

## Reporting

If you find a problem in this harness, open an issue on `ybedoyab/serqet`. This is not a channel for real hospital incidents. There is no production clinical system here.
