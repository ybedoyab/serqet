import Link from "next/link";
import { data, families } from "@/lib/data";

export default async function BenchmarksPage({
  searchParams,
}: {
  searchParams: Promise<{ family?: string; polarity?: string }>;
}) {
  const params = await searchParams;
  const family = params.family ?? "all";
  const polarity = params.polarity ?? "all";
  const scenarios = data.scenarios.filter((item) => {
    const familyOk = family === "all" || item.family === family;
    const polarityOk = polarity === "all" || item.polarity === polarity;
    return familyOk && polarityOk;
  });
  return (
    <div className="wrap hero">
      <p className="eyebrow">Tasks</p>
      <h1>Ten workflows, five twins</h1>
      <p>
        Every card is model status <strong>not measured</strong>. Open one to
        see the contract and the simulated oracle timeline.
      </p>
      <form className="filters" method="get">
        <label>
          Family
          <select name="family" defaultValue={family} aria-label="Filter by family">
            <option value="all">All families</option>
            {families().map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label>
          Polarity
          <select name="polarity" defaultValue={polarity} aria-label="Filter by polarity">
            <option value="all">Positive and negative</option>
            <option value="positive">Positive</option>
            <option value="negative">Negative</option>
          </select>
        </label>
        <button className="button" type="submit">
          Apply filters
        </button>
      </form>
      <div className="card-grid">
        {scenarios.map((item) => (
          <article className="card" key={item.scenario_id}>
            <p className="badge">{item.polarity}</p>{" "}
            <span className="badge warn">not measured</span>
            <h2>
              <Link href={`/benchmarks/${item.scenario_id}`}>{item.title}</Link>
            </h2>
            <p>{item.summary}</p>
            <p>
              {item.family_label} · seed {item.seed}
            </p>
          </article>
        ))}
      </div>
      {scenarios.length === 0 ? <p>No tasks match those filters.</p> : null}
    </div>
  );
}
