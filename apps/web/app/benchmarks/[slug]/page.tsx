import Link from "next/link";
import { notFound } from "next/navigation";
import { Timeline } from "@/components/Timeline";
import { data, scenarioById } from "@/lib/data";

export function generateStaticParams() {
  return data.scenarios.map((item) => ({ slug: item.scenario_id }));
}

export default async function ScenarioPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const scenario = scenarioById(slug);
  if (!scenario) {
    notFound();
  }
  return (
    <div className="wrap hero">
      <p className="eyebrow">{scenario.family_label}</p>
      <h1>{scenario.title}</h1>
      <p>
        <span className="badge">{scenario.polarity}</span>{" "}
        <span className="badge warn">model not measured</span>
      </p>
      <p>{scenario.summary}</p>
      <div className="detail-grid">
        <section>
          <h2>Staff request</h2>
          <p>{scenario.user_task}</p>
          <h2>Normative rule</h2>
          <p>{scenario.normative_rule}</p>
          <h2>Launch identity</h2>
          <ul>
            <li>Principal: {scenario.identity.principal_display}</li>
            <li>Tenant: {scenario.identity.tenant_id}</li>
            <li>Launch patient: {scenario.identity.launch_patient_id}</li>
            <li>Purpose: {scenario.identity.purpose}</li>
            <li>Scopes: {scenario.identity.scopes.join(", ")}</li>
          </ul>
          <h2>Authority schedule</h2>
          {scenario.schedule.length === 0 ? (
            <p>No mid-workflow change. The initial authority still holds at commit.</p>
          ) : (
            <ul>
              {scenario.schedule.map((item) => (
                <li key={item.reason}>
                  After tool call {item.after_tool_calls}: {item.reason}
                </li>
              ))}
            </ul>
          )}
        </section>
        <aside className="panel">
          <h2>Grader on the oracle replay</h2>
          <p>
            Pass: {scenario.demo.score.task_pass ? "yes" : "no"}. This score is
            the reference agent, not a model.
          </p>
          <p>
            <Link href="/benchmarks">All tasks</Link>
          </p>
        </aside>
      </div>
      <h2>Step through the oracle</h2>
      <Timeline events={scenario.demo.events} />
      <h2>Synthetic chart</h2>
      <div className="card-grid">
        {scenario.resources.map((resource) => (
          <details className="card" key={`${resource.resourceType}-${resource.id}`}>
            <summary>
              {resource.resourceType}/{resource.id}
            </summary>
            <pre>{JSON.stringify(resource, null, 2)}</pre>
          </details>
        ))}
      </div>
      <h2>Approval ledger</h2>
      <pre>{JSON.stringify(scenario.approvals, null, 2)}</pre>
    </div>
  );
}
