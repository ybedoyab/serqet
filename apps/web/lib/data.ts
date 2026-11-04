import bundle from "@/data/benchmarks.json";

export const data = bundle;

export type Scenario = (typeof bundle.scenarios)[number];

export function scenarioById(id: string): Scenario | undefined {
  return data.scenarios.find((item) => item.scenario_id === id);
}

export function families(): string[] {
  return [...new Set(data.scenarios.map((item) => item.family))];
}
