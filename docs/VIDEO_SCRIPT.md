# Video script

Target length: under five minutes. No face is required. Do not claim a model failed unless a measured trace is on screen. This script has not been recorded.

## Shot list

1. **0:00–0:30.** Title card: SERQET. Line: "Trust the action, not the answer." Say the question in one sentence: an agent can be allowed to start a hospital task and still be wrong if consent, approval, or the patient changes before it commits.
2. **0:30–1:20.** Show the ten task cards. Point at one positive and one negative twin. Say the policy is given to the agent; the test is not a hidden legal quiz.
3. **1:20–2:30.** Open `consent-revoked-before-commit` or `approval-withdrawn`. Play the simulated oracle timeline and say the banner means this is not a model. Show the environment step where consent or approval changes, then the re-check and the escalation. Contrast one sentence on the cached control, which keeps the first permit and fails.
4. **2:30–3:20.** Show the reckless control on a negative task: shadow mode changes state, enforced mode blocks the write, and both fail because the attempt counts. Say "blocked by the server" is not "the agent chose safely."
5. **3:20–4:10.** Open Models. Read the not-measured state out loud. Mention the oracle is 10/10 only as a harness check. If a real pilot exists by recording day, replace this shot with the actual model id, date, trial count, and one redacted trace. If it does not, leave the empty state.
6. **4:10–4:50.** Close on limits: synthetic data, FHIR R4 subset, no diagnosis, prior FHIR benchmarks already grade workflow success, SERQET asks about authority at commit time. Show the command `uv run serqet verify --offline`.

## On-screen labels to keep

- SIMULATED DEMO
- NOT_MEASURED, unless a real run is in `artifacts/measured`
- Reference controls, not model results
