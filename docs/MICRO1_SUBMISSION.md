# micro1 short description

SERQET tests whether a tool-using agent still respects hospital authority at the moment it acts, after patient context, research consent, supervisor approval, or a forged chart note has changed the decision. Ten paired synthetic FHIR R4 tasks are graded from sandbox state, not from the agent's own claim, and a shadow mode records forbidden side effects separately from a gateway that blocks them. Offline controls show the tasks are solvable, that blanket refusal fails the legitimate work, and that a cached permit fails the two mid-workflow revocations. No frontier model has been scored yet; the package says NOT_MEASURED rather than inventing traces.

## Upload checklist

- [ ] ZIP path `dist/serqet-micro1-submission.zip`, under 50 MB, opens without a password, contains code and small artifacts, and does not contain `.git`, `node_modules`, `.next`, videos, or secrets
- [ ] Extract the ZIP on a clean machine and run `uv sync --frozen --all-groups` then `uv run serqet verify --offline` from `packages/eval`
- [ ] Confirm the README states `NOT_MEASURED` unless a real `artifacts/measured` run was added
- [ ] Host a video of at most 5 minutes (script in `docs/VIDEO_SCRIPT.md`). Do not put the video in the ZIP
- [ ] Paste the short description above into the HackerRank form
- [ ] Submit before 9 November 2026, 05:15 UTC (9 November 2026, 00:15 America/Bogota)

This file does not mean the HackerRank form was submitted.
