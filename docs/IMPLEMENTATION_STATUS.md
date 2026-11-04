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

## Gate 6 — GitHub

- Pull request https://github.com/ybedoyab/serqet/pull/1 merged to `main` at `baac88d30bdc256bfb4c1174f54bcec51b3a0ae8` on 4 November 2026.
- CI run https://github.com/ybedoyab/serqet/actions/runs/41818242376 : python, web, and playwright all succeeded before the merge.

## Gate 7 — Vercel

- Project `serqet` (`prj_wi6jNoiNAsxZYA2rrz3iMxdq8hpn`) on team `ybedoyabs-projects`, root `apps/web`, production branch `main`, GitHub connected.
- Production deployment `dpl_G8aVNkPhytVfBSkCcwXN8Dy563tn` is READY from commit `0aac61daf9154a98cac218196f7a93d1d100a7a9`.
- Production aliases: https://serqet-liard.vercel.app and https://serqet-ybedoyabs-projects.vercel.app
- `/api/health` on both aliases returned `{"ok":true,"service":"serqet","commit":"0aac61daf9154a98cac218196f7a93d1d100a7a9"}`.
- Playwright against https://serqet-liard.vercel.app : 5 passed (overview, simulated timeline, empty model state, 390px viewport, health).
- `/api/health` reports whichever `main` commit is currently aliased. A later documentation commit can move that alias.

## Gate 8 — package

- `dist/serqet-micro1-submission.zip` is 96 files and 197624 bytes.
- Extracted tree passed `serqet verify --offline`. The ZIP is gitignored and is not a HackerRank upload.
