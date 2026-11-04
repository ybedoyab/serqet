# Research notes

Read on 4 November 2026 unless a row says otherwise. SERQET uses FHIR R4 4.0.1 field names only. R5-only elements are not copied into these resources.

## Distinctions that constrain the design

1. FHIR defines representations and REST semantics. It does not ship a universal authorization engine. The R4 security module is the frame; SERQET's oracle is a separate, explicit, synthetic policy.
2. A `Consent` resource records a directive. The R4 Consent page says enforcement is not included in the resource and is expected to use access-control mechanisms such as OAuth, UMA, or XACML. SERQET therefore stores `Consent` as evidence and decides in `policy.py`.
3. SMART patient scopes say what resource types an app may touch. Who the patient is comes from launch context. The SMART page also says access stays limited by the privileges of the user in context. A broad `patient/*.rs` token in SERQET does not cross tenants or patients.
4. `AuditEvent` records a security-relevant event (`type`, `recorded`, `agent` with `requestor`, `source.observer` are required in R4). `Provenance` records who changed a target (`target`, `recorded`, `agent.who` are required). SERQET writes an `AuditEvent` for authorized reads, authorized updates, and labeled violations. It writes `Provenance` only for authorized FHIR updates. A sentence in the agent's `finish` claim is not either resource.
5. Jurisdiction-specific consent law is not encoded here. `khepri-authority-v1` is a fictional hospital policy. It is not a HIPAA, GDPR, FDA, or EU AI Act claim. Purpose `TREAT` may read an observation without the research consent. Purpose `HRESCH` may write the internal disclosure ledger only while the matching `Consent` provision is active.
6. FHIR-AgentEval already grades FHIR workflow success against server state. LastEHR already checks a scripted approval gate. SERQET's addition is a scheduled authority change between check and commit, paired with a positive twin, scored separately from gateway enforcement.

## References

| Source | Date / version | URL | Design use | Limit |
| --- | --- | --- | --- | --- |
| FHIR R4 security module | R4 4.0.1 | https://hl7.org/fhir/R4/secpriv-module.html | Keep authorization outside the clinical resources | Not a ready-made policy engine |
| FHIR R4 Consent | R4 4.0.1, page read this session | https://hl7.org/fhir/R4/consent.html | `status`, `scope`, `category`, `patient`, `policyRule`, `provision.type/period/purpose/data` | Enforcement is explicitly out of scope for the resource |
| FHIR R4 AuditEvent | R4 4.0.1, cardinality checked this session | https://hl7.org/fhir/R4/auditevent.html | Sandbox-authored events, outcome `0` or `8` | Not a tamper-proof external log |
| FHIR R4 Provenance | R4 4.0.1, cardinality checked this session | https://hl7.org/fhir/R4/provenance.html | Authorized appointment updates only | Not a substitute for `AuditEvent` |
| SMART App Launch scopes | Scopes and launch context, read this session | https://www.hl7.org/fhir/smart-app-launch/scopes-and-launch-context.html | Patient context beats a broad token; scopes use `.cruds` letters | SERQET implements a subset, not an OAuth server |
| NIST AI RMF core | Measure function, page read this session | https://airc.nist.gov/airmf-resources/airmf/5-sec-core/ | Measure 2.6–2.8: document safety, security, and accountability tests and their limits | SERQET is a benchmark, not evidence that a deployed system meets the RMF |
| OWASP agentic top 10 | Page 9 Dec 2025; list branded 2026 | https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/ | ASI01 goal hijack (forged note), ASI02 tool misuse, ASI03 identity and privilege abuse | Mapping is illustrative, not an OWASP certification |
| FHIR-AgentEval | npj Digital Medicine, published 10 Oct 2026 | https://doi.org/10.1038/s41746-026-03348-0 | 43 resettable FHIR tasks; success plus state checks; memory helped tool choice. Differentiates SERQET | The published experiment is not an authority-drift or consent-revocation study. Code was not copied |
| FHIR-AgentEval repo | Accessed via the paper and search | https://github.com/YoussefMkst/FHIR-AgentEval | Confirms HAPI plus MCP CRUD and deterministic validators | Not executed here |
| MedAgentBench | Stanford repository; figures below are as quoted by FHIR-AgentEval, not re-run | https://github.com/stanfordmlgroup/MedAgentBench | Action tasks are harder than EHR question answering | This session did not re-execute the 300 tasks. Do not treat the quoted rates as SERQET results |
| FHIR-AgentBench | Cited by FHIR-AgentEval as read-only FHIR QA | Discussed in the FHIR-AgentEval paper | Shows read-only QA is a different bar than writes | The AgentBench paper itself was not re-read in this session |
| LastEHR FHIR Agent Safety Eval | Updated 9 Oct 2026, page read this session | https://www.lastehr.com/docs/evals | Scripted propose / approve / deny / cleanup on synthetic charts. Explicitly not RBAC or prompt-injection certification | Different harness and claim. Not copied |
| micro1 FAQ | Read 4 Nov 2026 | https://www.micro1.ai/hackathon/faq | 5–10 tasks, code-only ZIP ≤ 50 MB, separate video ≤ 5 min, no fabricated results, disclose earlier work | The HackerRank instructions tab was not available without the event login |

FHIR-AgentEval's paper, as retrieved from the PMC abstract and discussion, reports a 43-task sandbox (appointment management and genetic testing), resettable FHIR state, and a memory ablation whose best held-out gain was 9.1% over its baseline. It also summarizes MedAgentBench as roughly 70% for the best model overall, about 85.33% on query-style tasks and 54% on action tasks. Those numbers are theirs. SERQET did not reproduce them.

## What was not checked

- The full HackerRank instructions tab behind the event login.
- A live HAPI FHIR validation of every fixture. The local checker covers the R4 fields this suite reads and writes.
- Any model API, at the time these design notes were written. That check is historical. The later measurement is `docs/FRONTIER_MODEL_FINDINGS.md`, status `MEASURED`, 31 accepted trials. This notes file did not re-execute FHIR-AgentEval or MedAgentBench.
