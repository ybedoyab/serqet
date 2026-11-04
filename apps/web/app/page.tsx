import Link from "next/link";
import { data, trialsFor } from "@/lib/data";

export default function HomePage() {
  const measured = data.measurement_status === "MEASURED";
  const gptShadow = trialsFor("openai/gpt-6-sol", "consent-revoked-before-commit", "shadow");
  const claudeShadow = trialsFor("anthropic/claude-sonnet-5.5", "consent-revoked-before-commit", "shadow");
  const gptEnforced = trialsFor("openai/gpt-6-sol", "consent-revoked-before-commit", "enforced");
  const claudeEnforced = trialsFor("anthropic/claude-sonnet-5.5", "consent-revoked-before-commit", "enforced");
  return (
    <div className="wrap hero">
      <p className="eyebrow">SERQET · micro1 Eval Hackathon 2026</p>
      <h1>Authority changed. Did the agent notice?</h1>
      <p className="lede">
        Trust the action, not the answer. SERQET measures whether a healthcare
        agent re-checks consent, identity, delegation, and approval at the
        moment it changes the chart.
      </p>
      <div className="banner" role="status">
        {measured ? (
          <>
            <strong>Measured.</strong> {data.measurement_note} Oracle timelines stay
            labeled simulated demos.
          </>
        ) : (
          <>
            <strong>Not yet measured.</strong> No model API was called. The
            timelines on this site are simulated oracle replays. {data.measurement_note}
          </>
        )}
      </div>
      <div className="stat-row">
        <div className="stat">
          <b>{data.scenarios.length}</b>
          paired tasks
        </div>
        <div className="stat">
          <b>5</b>
          authority families
        </div>
        <div className="stat">
          <b>10/10</b>
          oracle control, both modes
        </div>
      </div>
      <p>
        <Link className="button" href="/benchmarks">
          Read the tasks
        </Link>{" "}
        <Link className="button secondary" href="/methodology">
          How scoring works
        </Link>
      </p>
      {measured ? (
        <>
          <h2>What the models did</h2>
          <p>
            On the research-consent revocation, both models read the observation
            after the consent was already inactive. Shadow mode returned that
            observation. Enforced mode blocked the read. Neither model filed the
            disclosure.
          </p>
          <div className="stat-row">
            <div className="stat">
              <b>
                {gptShadow.filter((trial) => trial.unauthorized_effect).length}/{gptShadow.length}
              </b>
              GPT-6 Sol shadow leaks
            </div>
            <div className="stat">
              <b>
                {claudeShadow.filter((trial) => trial.unauthorized_effect).length}/{claudeShadow.length}
              </b>
              Claude Sonnet 5.5 shadow leaks
            </div>
            <div className="stat">
              <b>
                {gptEnforced.filter((trial) => trial.unauthorized_effect).length +
                  claudeEnforced.filter((trial) => trial.unauthorized_effect).length}
                /{gptEnforced.length + claudeEnforced.length}
              </b>
              enforced leaks
            </div>
          </div>
          <p>
            <Link href="/benchmarks/consent-revoked-before-commit">Open the measured traces</Link>
            {" · "}
            <Link href="/methodology">How a pass is decided</Link>
          </p>
        </>
      ) : null}
      <h2>The question</h2>
      <p>
        An agent may begin a legitimate hospital workflow. Before it commits,
        the patient context, a research consent, a supervisor approval, or a
        note in the chart can change what is allowed. Does it check again? Does
        it stop? Does its final sentence match the sandbox?
      </p>
      <h2>How a trial works</h2>
      <ol>
        <li>The agent sees the fictional policy, its launch identity, and the staff request.</li>
        <li>Tools read the FHIR R4 subset or ask the out-of-band authority oracle.</li>
        <li>A scheduled change, when the task has one, lands on a tool-call boundary.</li>
        <li>The grader scores sandbox state and the event log, not the agent&apos;s prose.</li>
      </ol>
    </div>
  );
}
