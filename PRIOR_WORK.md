# Prior work

SERQET was written for the micro1 Eval Hackathon, 30 October through 9 November 2026. The repository began as an empty initial commit (`2e3bcbd`, README text `# serqet` / `micro1`). Everything under this tree except that one-line README is new work from this window.

## EIR

`https://github.com/ybedoyab/eir` (EIR — Healthcare Agent Fleet) is earlier work by the same person. It used patient access and scheduling, FHIR R4, human review, and synthetic clinical data in a different hackathon. That experience suggested the research question: agents that sound authorized can still act after consent, scope, or approval has changed.

EIR is background context only. This repository does not copy EIR source, prompts, fixtures, infrastructure, or cloud configuration. SERQET's sandbox, policy engine, scenarios, grader, and dashboard were written here. Do not treat SERQET as a patch, fork, or deployment of EIR.

## Other public evals

Two public micro1-era repositories were checked at the title and description level on 4 November 2026, not copied:

- `Nahuel990/ministack-agentic-eval` — an agentic eval on AWS using Ministack. Different domain and harness.
- `dl88jing/micro1-frontier-evals` — PyScope, a Python scoping (LEGB / class-body) eval. Different domain.

The shared idea is a deterministic grader over observable behavior. The tasks are not shared.

FHIR-AgentEval, MedAgentBench, FHIR-AgentBench, and the LastEHR FHIR Agent Safety Eval are prior art in clinical or FHIR agent evaluation. They are cited in [docs/RESEARCH.md](docs/RESEARCH.md). None of their tasks, prompts, or code are vendored here.
