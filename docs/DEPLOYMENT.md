# Deployment

The website is a read-only Next.js app. The Python evaluator stays on the operator's machine. Do not deploy a public FHIR sandbox or a public model proxy.

## Local

```bash
cd packages/eval && uv run serqet verify --offline
cd apps/web && npm ci && npm run build && npm run start
```

`/api/health` returns `VERCEL_GIT_COMMIT_SHA` on Vercel, then `NEXT_PUBLIC_COMMIT_SHA`, then `dev`.

## Vercel

- Team: `ybedoyabs-projects` (`team_7T0tWNqJuCNscCRtNnAyPi1j`)
- Project name: `serqet`
- Root directory: `apps/web`
- Production branch: `main`
- No required environment variables. Do not add provider keys to the project.

Production, observed 4 November 2026 from deployment `dpl_G8aVNkPhytVfBSkCcwXN8Dy563tn` (commit `0aac61daf9154a98cac218196f7a93d1d100a7a9`):

- https://serqet-liard.vercel.app
- https://serqet-ybedoyabs-projects.vercel.app

Both aliases returned that commit from `/api/health`. Playwright passed against the first URL. A preview deployment URL is not the production address.
