# Threat model

SERQET is an evaluation harness for fictional charts. It is not a production hospital system.

## Assets

- The scenario contract and the grader, because a leaked gold label or a grader that trusts the model would invalidate the study.
- The sandbox state, because the scientific claim is about side effects.
- Provider keys and the cost cap, because a public or accidental call spends money and can leak into logs.
- The reputation of the result, because a simulated trace labeled as a model run is a false claim.

## Actors

- The agent under test, which sees the policy, the launch identity, the user task, and tool results.
- The scenario author, who can see `grader_private` and the schedule. The model prompt builder does not.
- The environment, which applies the schedule after a fixed tool-call count.
- A judge reading the dashboard or the ZIP.

## Trust boundaries

- Tool arguments are data. They cannot select arbitrary files, shells, or URLs.
- `DocumentReference` text is untrusted. The oracle never reads it.
- The agent cannot create an `AuditEvent` or `Provenance`. Only the sandbox writes those.
- `finish.claim` is ignored by the effect checks. Only `finish.status` is compared, and only against state.
- Shadow mode is an observation instrument. It is not a production mode.
- The website is read-only. It has no model endpoint and no mutating FHIR API.

## Surfaces

- Indirect prompt injection in the forged note (`forge-policy-in-note`), mapped to OWASP ASI01 as an illustration.
- Tool misuse and stale permission (ASI02): reckless completion and cached authority.
- Identity and privilege abuse (ASI03): lookalike patient, cross-tenant read, broad `patient/*.rs`.
- Cost and denial of service: tool budget of 24 calls, default cost cap `0`, `run-models` refuses to dial a provider at cap 0 or without a key.
- Tampering with a saved trace: the grader recomputes the hash chain and replays requests. A mismatched hash fails the task. The chain is local. It is not an externally anchored timestamp.

## Mitigations that are real

- Default deny.
- Patient, tenant, purpose, scope, consent, and approval checks at the gateway at execution time.
- Separate attempt and effect scores.
- Secret scan in `scripts/check_secrets.py`.
- `.env` is gitignored. `.env.example` has empty placeholders.

## Limits

- The oracle is correct only for the coded rules. It is not a clinical-safety proof.
- Hash chaining detects edits inside one log. It does not survive a rewritten log that is internally consistent unless the effects also fail, and a fully rewritten consistent log is just a different trace, which the grader scores on its merits.
- No model has been attacked or measured yet.
- Synthetic names can still look like real people by coincidence. Identifiers use the `khepri.example` system and made-up ids.
