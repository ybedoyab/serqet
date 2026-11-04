import { data } from "@/lib/data";

export default function ModelsPage() {
  const controls = Object.entries(data.controls);
  return (
    <div className="wrap hero">
      <p className="eyebrow">Empirical comparison</p>
      <h1>No model has been scored</h1>
      <div className="banner" role="status">
        <strong>{data.measurement_status}.</strong> {data.measurement_note}
      </div>
      {data.models.length === 0 ? (
        <p>
          There is no model id, provider date, trial count, or token cost to
          show. A blank table would look like a result, so this page does not
          draw one.
        </p>
      ) : null}
      <h2>Reference controls</h2>
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
