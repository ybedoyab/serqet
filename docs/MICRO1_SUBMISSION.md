# micro1 short description

SERQET evaluates whether frontier AI agents respect dynamic authorization during synthetic FHIR hospital workflows. Ten paired scenarios are graded deterministically from tool actions and sandbox state, not from the agent's final sentence. Across 31 validated trials, GPT-6 Sol and Claude Sonnet 5.5 both requested a research observation after consent had become inactive, in 3/3 shadow trials each. Shadow mode returned the synthetic observation. An enforced gateway blocked the same read and returned no observation. Neither model filed a disclosure. The prompt requires a commit-time recheck. It does not explicitly require a fresh authorization call before every read, and the revocation is not announced before the next tool call. The live policy denied the read anyway. This is a synthetic authorization result, not a hospital breach and not a regulatory finding.

## Shorter alternative

SERQET grades whether frontier agents respect changing authorization in synthetic FHIR workflows. Ten paired tasks are scored from tool actions and sandbox state. In 31 validated trials, GPT-6 Sol and Claude Sonnet 5.5 each requested a research observation after consent was inactive, on 3/3 shadow trials. Shadow mode returned the synthetic row. An enforced gateway blocked it. Neither model filed a disclosure. A safe-sounding final answer did not replace server-side access control.

## Upload checklist

- [ ] ZIP path `dist/serqet-micro1-submission.zip`, under 50 MB, generated from the release tree, with no `.env`, `.git`, `artifacts/budget`, videos, or secrets
- [ ] Extract the ZIP in a clean directory and run `uv sync --project packages/eval --frozen --all-groups`, then `uv run --project packages/eval serqet audit`
- [ ] Confirm the README states `MEASURED`, links the findings, and links the public walkthrough URL
- [x] Host a video of at most 5 minutes. The public file is https://github.com/ybedoyab/serqet/releases/download/walkthrough-2026-11-04/serqet-walkthrough.mp4. Do not put the video in the ZIP
- [ ] Paste one of the descriptions above into the HackerRank form
- [ ] Submit before 9 November 2026, 05:15 UTC (9 November 2026, 00:15 America/Bogota)

This file does not mean the HackerRank form was submitted. No additional OpenRouter call is part of this checklist.
