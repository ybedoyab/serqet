export default function AboutPage() {
  return (
    <div className="wrap hero">
      <p className="eyebrow">About</p>
      <h1>A benchmark, not a clinic</h1>
      <p>
        SERQET was written for the micro1 Eval Hackathon, October 30 to
        November 9, 2026. The charts are synthetic. Identifiers use
        khepri.example. Nothing here diagnoses, prescribes, or messages a real
        person.
      </p>
      <h2>Prior art</h2>
      <p>
        FHIR-AgentEval, MedAgentBench, and the LastEHR safety harness already
        test FHIR actions or approval mechanics. SERQET asks a narrower
        question: when authority changes in the middle of a legitimate
        workflow, does the agent notice before the side effect? That claim
        is now measured for two OpenRouter models. The traces and the limits are
        in the repository findings.
      </p>
      <h2>Earlier work by the author</h2>
      <p>
        EIR, a previous healthcare-agent project, is experience only. Its code,
        fixtures, and deployments are not in this repository. The micro1
        participant agreement licenses submitted work to the organizer; that is
        why proprietary material was left out.
      </p>
      <p>
        Source and citations live in the GitHub repository{" "}
        <a href="https://github.com/ybedoyab/serqet">ybedoyab/serqet</a>.
      </p>
    </div>
  );
}
