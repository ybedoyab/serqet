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

The production URL, when one exists, is recorded in `docs/IMPLEMENTATION_STATUS.md` after a deploy is actually observed. A preview URL is not production.
