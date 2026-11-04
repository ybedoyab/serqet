# QA report

This report replaces the foundation QA note. The commands below were run on 4 November 2026 against the finalization tree. Older counts in git history, including 13 pytest tests and a 96-file ZIP, describe earlier commits. They are not the current result.

## Python

- `uv run --project packages/eval ruff check packages/eval` — pass
- `uv run --project packages/eval mypy packages/eval/serqet` — pass, 20 source files
- `uv run --project packages/eval pytest -q` — 31 passed
- `uv run --project packages/eval serqet audit` — exit 0
  - accepted 31, rejected 0, task passes 19, cost USD 0.547108
  - GPT-6 Sol shadow 11/14, enforced 0/1
  - Claude Sonnet 5.5 shadow 8/14, enforced 0/2
  - evidence rollup matched the frozen JSON bytes
- `python scripts/check_secrets.py` — the only match is the local `.env`, which `.gitignore` excludes. Every other file in the tree had no credential prefix. `.env` is not part of the commit or the ZIP.

`audit` does not call a provider and does not rewrite `artifacts/measured`.

## Web

- `npm ci` in `apps/web` — completed from the lockfile
- `npm run lint` — pass, no ESLint warnings or errors
- `npm run typecheck` — pass
- `npm run build` — pass, Next.js 15.5.29. Pages are server-rendered on demand so the CSP nonce can be stamped on script tags. `/icon.svg` stays static.
- `npm run test:e2e` — 7 passed. Covered the measured overview, a simulated timeline and a measured timeline step, the model matrix, a 390px viewport, keyboard focus, a 768px viewport, and `/api/health`

Before this pass, scenario pages were prerendered without a nonce while middleware sent a nonce CSP, so the timeline buttons did not run in a browser that enforces CSP. The root layout now reads the request nonce and the pages render dynamically. Playwright was rerun after that change.

## What this report does not include yet

The submission ZIP, the GitHub Actions run for this branch, and the production deployment are recorded in `docs/FINAL_SUBMISSION_AUDIT.md` after those steps finish. No new OpenRouter call was made for this QA pass.
