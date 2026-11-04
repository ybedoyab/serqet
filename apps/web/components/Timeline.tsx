"use client";

import { useState } from "react";

type DemoEvent = {
  step: number;
  logical_time: string;
  actor: string;
  tool: string;
  outcome: string;
  permission: { permit?: boolean; reason?: string } | null;
  request: Record<string, unknown>;
  result: Record<string, unknown>;
};

export function Timeline({
  events,
  label = "SIMULATED DEMO",
  note = "Oracle replay. This is not a frontier-model trace.",
}: {
  events: DemoEvent[];
  label?: string;
  note?: string;
}) {
  const [index, setIndex] = useState(0);
  const event = events[index];
  if (!event) {
    return <p>This demo has no steps.</p>;
  }
  return (
    <div>
      <p className="badge">{label}</p>
      <p>{note}</p>
      <div className="timeline-controls">
        <button
          type="button"
          className="button secondary"
          onClick={() => setIndex((value) => Math.max(0, value - 1))}
          disabled={index === 0}
        >
          Previous step
        </button>
        <button
          type="button"
          className="button secondary"
          onClick={() => setIndex((value) => Math.min(events.length - 1, value + 1))}
          disabled={index === events.length - 1}
        >
          Next step
        </button>
        <span>
          Step {index + 1} of {events.length}
        </span>
      </div>
      <article className="panel" aria-live="polite">
        <h3>
          {event.tool}{" "}
          <span className="badge">{event.outcome}</span>
        </h3>
        <p>
          {event.logical_time} · {event.actor}
        </p>
        <p>
          Authority:{" "}
          {event.permission
            ? `${event.permission.permit ? "permit" : "deny"} (${event.permission.reason})`
            : "not a permission check"}
        </p>
        <h4>Request</h4>
        <pre>{JSON.stringify(event.request, null, 2)}</pre>
        <h4>Result</h4>
        <pre>{JSON.stringify(event.result, null, 2)}</pre>
      </article>
      <ol className="step-list">
        {events.map((item, itemIndex) => (
          <li key={`${item.tool}-${item.step}-${itemIndex}`}>
            <button
              type="button"
              aria-current={itemIndex === index ? "step" : undefined}
              onClick={() => setIndex(itemIndex)}
            >
              {item.logical_time} · {item.tool} · {item.outcome}
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}
