# QA report

Updated as gates finish. Commands below were run on 4 November 2026 unless a later section says otherwise.

## Python

- `uv run --project packages/eval ruff check packages/eval` — pass
- `uv run --project packages/eval mypy packages/eval/serqet` — pass, 15 files
- `uv run --project packages/eval pytest` — 13 passed
- `uv run --project packages/eval serqet verify --offline` — exit 0

Control matrix from that verify:

- oracle_agent shadow 10/10, enforced 10/10
- always_refuse shadow 5/10, enforced 5/10
- reckless_completer shadow 5/10, enforced 5/10
- cached_authority_agent shadow 8/10, enforced 8/10
- measurement_status `NOT_MEASURED`

## Web

- `npm run typecheck` in `apps/web` — pass
- `npm run lint` — pass, no ESLint warnings
- `npm run build` — pass, Next.js 15.5.29, 20 static pages including all 10 scenario routes
- `npm run test:e2e` — 5 passed. Covered the overview question, the not-measured banner, a scenario timeline labeled SIMULATED DEMO, the empty model state, a 390px viewport without horizontal overflow, and `/api/health`

The first end-to-end run failed because a static `script-src 'self'` policy blocked Next.js inline bootstrap scripts and the hydrated page lost its headings. Middleware now sets a per-request nonce. The rerun passed.

## Secret scan and ZIP

- `python scripts/check_secrets.py` — pass, no credential prefixes
- `uv run --project packages/eval serqet package --output dist/serqet-micro1-submission.zip` — 96 files, 197624 bytes
- The extracted tree ran `serqet verify --offline` and the controls still separated

## GitHub and production

- CI https://github.com/ybedoyab/serqet/actions/runs/41818242376 — python, web, and playwright passed. Pull request https://github.com/ybedoyab/serqet/pull/1 merged.
- Production https://serqet-liard.vercel.app (`dpl_G8aVNkPhytVfBSkCcwXN8Dy563tn`, commit `0aac61daf9154a98cac218196f7a93d1d100a7a9`). The same Playwright file, pointed at that origin, passed 5 tests. Health returned that commit.
