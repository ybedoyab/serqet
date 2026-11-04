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

- `MEASURED` on 4 November 2026. 31 accepted OpenRouter trials, 0 rejected. Provider usage USD 0.5471084. Details in `docs/FRONTIER_MODEL_FINDINGS.md`.

## Gate 4 — dashboard

- Next.js app in `apps/web`. The first local Playwright run was 5 tests, before measured traces were on the page.
- At that time the models page stated `NOT_MEASURED` and scenario timelines were only SIMULATED DEMO. After the 4 November measurement, model traces are labeled MEASURED MODEL RESULT and the oracle timeline remains SIMULATED DEMO. Current test counts are in `docs/QA_REPORT.md`.

## Gate 5 — quality

- Python ruff, mypy, and pytest passed locally. Web lint, typecheck, build, and Playwright passed locally.
- Content-Security-Policy is set in middleware with a nonce so Next can boot without `'unsafe-inline'` scripts.

## Gate 6 — GitHub

- Pull request https://github.com/ybedoyab/serqet/pull/1 merged to `main` at `baac88d30bdc256bfb4c1174f54bcec51b3a0ae8` on 4 November 2026.
- CI run https://github.com/ybedoyab/serqet/actions/runs/41818242376 : python, web, and playwright all succeeded before the merge.

## Gate 7 — Vercel

- Project `serqet` (`prj_wi6jNoiNAsxZYA2rrz3iMxdq8hpn`) on team `ybedoyabs-projects`, root `apps/web`, production branch `main`, GitHub connected.
- Production deployment `dpl_3UEbHdeVyznPzVi4zw3ZZE8ekiLx` is READY from merge `232d797b14f3ec5420bd03ebdc70dfe23dfcef33`.
- `/api/health` returned that commit. Playwright against https://serqet-liard.vercel.app passed 5 tests on that deployment: overview, simulated timeline, empty model page, 390px viewport, and health.
- The earlier foundation deployment remains `dpl_EcAJ2u99Tii5YqgZTfEMycyp52rh` at `efd1b90a57dd780e0636258c9cbcf0735341b720`.
- Production aliases: https://serqet-liard.vercel.app and https://serqet-ybedoyabs-projects.vercel.app
- `/api/health` on both aliases returned the commit that was current at the time of that check. A later commit on `main` moves the alias; read `/api/health` for the live SHA.

## Phase 2 — harness and validity

- Dataset `serqet-2026-11-04.2`. Revocation on the two negative twins is applied before the commit decision. Control pass counts are unchanged: oracle 10/10, always-refuse 5/10, reckless 5/10, cached 8/10.
- The multi-turn runner, provider routing, budget check, and measured-record validator are in the package. Mocked tests cover them.
- When this section was written, no paid call had been authorized and the status was `NOT_MEASURED`. That was the pre-measurement state. The later run is Gate 3 above: 31 accepted trials, provider-reported trial cost USD 0.547108. No further paid call is part of the submission finalization.
- See `docs/VALIDITY_AUDIT.md` and `docs/EVAL_RUNBOOK.md`.

## Gate 8 — package

- `dist/serqet-micro1-submission.zip` rebuilt from `232d797b14f3ec5420bd03ebdc70dfe23dfcef33`: 101 files, 217279 bytes.
- The extracted tree passed `serqet verify --offline`. The ZIP is gitignored and is not a HackerRank upload.
