# Implementation status

## Gate 0 — inspect

- Repo `https://github.com/ybedoyab/serqet`, branch work started from `main` at `2e3bcbdbb59293e383d5d4fec4c96dd2d9954ded`.
- Working tree was only `README.md` (`# serqet` / `micro1`).
- GitHub CLI authenticated as `ybedoyab`. No model API keys and no `.env`.
- `npx vercel` CLI 65.11.0 already logged in as `ybedoyab`. Team `ybedoyabs-projects`. No existing Vercel project named `serqet`.
- Feature branch: `feat/serqet-eval-foundation`.

## Gate 1 — specification

- Research, policy, threat model, task catalog, and ten scenario JSON files are in the tree.
- Policy is `khepri-authority-v1`. FHIR subset is R4. Ledgers are explicitly non-FHIR.

## Gate 2 — offline evaluator

- Done. `serqet verify --offline` exit 0 on 4 November 2026.
- oracle 10/10 shadow and enforced. always-refuse 5/10. reckless 5/10. cached authority 8/10 (fails the two TOCTOU negatives).

## Gate 3 — models

- `NOT_MEASURED`. No key. Cost cap default 0. `run-models` without `--dry-run` exits 2 and does not open a provider socket.

## Gate 4 — dashboard

- Next.js app in `apps/web`. Local Playwright: 5 passed, including desktop task navigation and a 390px viewport.
- Models page states `NOT_MEASURED`. Scenario timelines are labeled SIMULATED DEMO.

## Gate 5 — quality

- Python ruff, mypy, and pytest passed locally. Web lint, typecheck, build, and Playwright passed locally.
- Content-Security-Policy is set in middleware with a nonce so Next can boot without `'unsafe-inline'` scripts.

## Gates 6–9

- GitHub, Vercel, and the ZIP size are filled in after those commands return. They are not claimed yet.
