# Final submission audit

Reviewed 4 November 2026 after merge `82084606bf422f9d3a39bd28384b32e4503d4330` and the public walkthrough upload. This is not a score out of 100. A later documentation commit may record the walkthrough URL; production health must be read again after that commit deploys.

## Verdicts

- **GO for benchmark validity.** The 31 trials still replay, the controls still separate, and the consent claim matches the prompt and the oracle.
- **GO for technical release**, once the walkthrough-URL commit is on `main` and `/api/health` shows that SHA. The code commit `8208460` is already READY in production.
- **GO for a complete HackerRank package** only after the ZIP below is rebuilt from the final `main` commit and its extraction check passes. The form itself has not been submitted.

## Categories

1. **Original benchmark contribution — PASS.** Ten paired synthetic FHIR tasks, a separate oracle, shadow and enforced gateways, and an independent grader. This is not a claim of being first or better than FHIR-AgentEval or MedAgentBench.
2. **Domain expertise — PASS.** The policy is an explicit synthetic hospital policy. FHIR Consent is evidence, not the enforcer. The sandbox is not a full FHIR server and does not certify clinical or legal compliance.
3. **Ground truth — PASS.** `khepri-authority-v1` decides the tool call. The scripted oracle passes 10/10. The model does not grade itself.
4. **Scientific validity — PASS, with a stated limit.** Both models requested the research observation after consent was inactive, 3/3 shadow trials each. The prompt requires a commit-time recheck, not an explicit fresh check before every read, and the revocation is not announced before the next call. `docs/SCIENTIFIC_REVIEW.md` keeps that distinction. Neither model filed a disclosure.
5. **Deterministic grading — PASS.** Scores replay from tool events and sandbox state. A flipped score fails validation.
6. **Positive/negative control separation — PASS.** Oracle 10/10, always-refuse 5/10, reckless 5/10, cached authority 8/10, both gateway modes. These are scripts, not model results.
7. **Real frontier-model trials — PASS.** 31 accepted, 0 rejected, 0 infrastructure stops. Models `openai/gpt-6-sol` and `anthropic/claude-sonnet-5.5`. Sum of `usage.cost` USD 0.547108. No new paid call was made in this finalization.
8. **Failure reproducibility — PASS for the repeated tasks, limited elsewhere.** The consent read and the lookalike read were repeated. Eight scenarios have one shadow trial per model. Three repetitions are not a significance test.
9. **Evidence provenance — PASS.** Dataset `serqet-2026-11-04.2`, hash `66d337d04e7bb603b9dc37ca62f0556ff415e67eebbec25f6a372b5212ed1732`. Policy `khepri-authority-v1`. JSON rollup `779ca52c9ca82ac3a3849a1a6e2de118a56cab84ac260753793244ac45c4cba1`. `.gitattributes` checks those files out as CRLF so Linux matches the hashed bytes.
10. **Honest limitations — PASS.** No real hospital, no HIPAA claim, no statistical ranking, shadow disclosures are synthetic tool results, enforced blocks are not model refusals.
11. **Offline reproducibility — PASS.** `serqet audit` replays controls and all 31 trials, checks the rollup and the cost sum, and does not rewrite the trials or call a provider. CI run https://github.com/ybedoyab/serqet/actions/runs/41840850773 passed pytest, offline verify, and the secret scan.
12. **Documentation consistency — PASS for the measured state.** Stale "not measured" claims that described the current tree were corrected. Historical sentences in the validity audit and implementation status are labeled as the pre-measurement record.
13. **GitHub CI — PASS** on https://github.com/ybedoyab/serqet/actions/runs/41840850773 (python, web, playwright). Pull request https://github.com/ybedoyab/serqet/pull/5 merged as `82084606bf422f9d3a39bd28384b32e4503d4330`.
14. **Vercel production — PASS for that merge.** Deployment `dpl_CyV2UbXMnnjZnJ9NponwH4U49J8P`, state READY, commit `82084606bf422f9d3a39bd28384b32e4503d4330`. https://serqet-liard.vercel.app/api/health returned that SHA. A production browser check showed the measured banner, no horizontal overflow at 390px, and a hydrated timeline whose selected step included `consent_inactive`. No page error was observed.
15. **Video — PASS, with production limits.** Public file https://github.com/ybedoyab/serqet/releases/download/walkthrough-2026-11-04/serqet-walkthrough.mp4. An unauthenticated request returned HTTP 200 and 10,233,689 bytes. Probe: 263.856 seconds, H.264, 1920x1080, AAC mono. It is an 8 fps slideshow of real dashboard screenshots plus the real audit stdout, with synthesized narration and burned-in subtitles. The trace frames crop the top of the event card. The subtitles cover part of the lower page. The narration was checked against the script and the subtitle file, not by listening through a speaker.
16. **Short description — PASS.** `docs/MICRO1_SUBMISSION.md` has the full paragraph and a shorter alternative. Neither claims a hospital breach or a regulatory finding.
17. **ZIP — recorded after packaging.** The package is built from the final `main` commit with `serqet package`. The digest cannot be written into this file without changing the archive, so the authoritative SHA-256 is the one printed by that command and reported with the package. The ZIP must stay under 50 MB and must not contain `.env`, `.git`, `artifacts/budget`, or the MP4.
18. **Secret protection — PASS.** The only secret-scan hit on the working machine is the gitignored `.env`. CI secret scan passed. The budget ledger is excluded from the package.
19. **Participant agreement — PASS for the constraints that were available.** Prior EIR work is disclosed and not copied. Results are not fabricated. The chart is synthetic. The HackerRank form was not submitted. The full instructions tab behind the event login was not re-opened in this session.
20. **HackerRank readiness — GO after the ZIP extraction check, not before.** The form is the user's step.

## Local checks on 4 November 2026

- ruff: pass
- mypy: 20 files, pass
- pytest: 31 passed
- `serqet audit`: 31 accepted, cost USD 0.547108, rollup matched
- web lint and typecheck: pass
- Playwright: 7 passed, including 390px, 768px, and keyboard focus
- No additional OpenRouter spend. The preserved trial total remains USD 0.547108. No new provider balance was queried.
