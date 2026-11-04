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

Production, observed 4 November 2026 from deployment `dpl_3UEbHdeVyznPzVi4zw3ZZE8ekiLx` (commit `232d797b14f3ec5420bd03ebdc70dfe23dfcef33`):

- https://serqet-liard.vercel.app
- https://serqet-ybedoyabs-projects.vercel.app

Both aliases returned that commit from `/api/health`. Playwright passed against the first URL. A preview deployment URL is not the production address.
