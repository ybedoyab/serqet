import { data, measuredModels } from "@/lib/data";

export default function ModelsPage() {
  const controls = Object.entries(data.controls);
  const measured = data.measurement_status === "MEASURED" ? measuredModels() : [];
  return (
    <div className="wrap hero">
      <p className="eyebrow">Empirical comparison</p>
      {measured.length === 0 ? (
        <>
          <h1>No model has been scored</h1>
          <div className="banner" role="status">
            <strong>{data.measurement_status}.</strong> {data.measurement_note}
          </div>
          <p>
            There is no model id, provider date, trial count, or token cost to
            show. A blank table would look like a result, so this page does not
            draw one.
          </p>
        </>
      ) : (
        <>
          <h1>Measured model results</h1>
          <div className="banner" role="status">
            <strong>MEASURED MODEL RESULT.</strong> {data.measurement_note}
          </div>
          <p>
            {measured.length} validated trials. Repeated failures are three shadow
            trials of the same task, so a trial-weighted pass rate is lower than
            a scenario-weighted one. Each card is one trial. Cost figures are
            provider-reported and are not a billing guarantee.
          </p>
          <div className="card-grid">
            {measured.map((trial) => (
              <article className="card" key={`${trial.model}-${trial.scenario_id}-${trial.mode}-${trial.trial}`}>
                <p className="badge">MEASURED MODEL RESULT</p>
                <h2>
                  {trial.provider}/{trial.model}
                </h2>
                <ul>
                  <li>
                    {trial.scenario_id} · {trial.mode} · trial {trial.trial}
                  </li>
                  <li>
                    {trial.started_at} to {trial.finished_at}
                  </li>
                  <li>Dataset {trial.dataset_version}</li>
                  <li>Policy {trial.policy_version}</li>
                  <li>Pass: {trial.task_pass ? "yes" : "no"}</li>
                  <li>
                    Unauthorized attempt: {trial.unauthorized_attempt ? "yes" : "no"}; effect:{" "}
                    {trial.unauthorized_effect ? "yes" : "no"}
                  </li>
                  <li>
                    Cost USD {trial.cost_usd} ({trial.cost_is_billing_guarantee ? "guarantee" : "not a billing guarantee"})
                  </li>
                  <li>
                    Tokens in {trial.usage.prompt_tokens ?? 0}, out {trial.usage.completion_tokens ?? 0}
                  </li>
                  <li>{trial.failure_reasons.join(", ") || "no failure flags"}</li>
                </ul>
              </article>
            ))}
          </div>
        </>
      )}
      <h2>Reference controls</h2>
      <p className="badge">REFERENCE CONTROL</p>
      <p>
        These pass counts come from scripted agents in the offline suite. They
        show the tasks can separate careful, refusing, reckless, and stale
        behavior. They are not a leaderboard.
      </p>
      <div className="card-grid">
        {controls.map(([agent, modes]) => (
          <article className="card" key={agent}>
            <h3>{agent}</h3>
            <ul>
              {Object.entries(modes).map(([mode, payload]) => (
                <li key={mode}>
                  {mode}: {payload.passed}/{payload.total}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  );
}
