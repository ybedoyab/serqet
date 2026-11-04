import bundle from "@/data/benchmarks.json";

export const data = bundle;

export type Scenario = (typeof bundle.scenarios)[number];

export type MeasuredTrial = {
  label: string;
  provider: string;
  model: string;
  started_at: string;
  finished_at: string;
  scenario_id: string;
  mode: string;
  trial: number;
  dataset_version: string;
  policy_version: string;
  stop_reason: string;
  cost_usd: number;
  cost_is_billing_guarantee: boolean;
  usage: { prompt_tokens?: number; completion_tokens?: number };
  task_pass: boolean;
  failure_reasons: string[];
  unauthorized_attempt: boolean;
  unauthorized_effect: boolean;
  authorized_completion: boolean;
  correct_escalation: boolean;
  false_refusal: boolean;
  false_success_claim: boolean;
  events: Scenario["demo"]["events"];
};

export function scenarioById(id: string): Scenario | undefined {
  return data.scenarios.find((item) => item.scenario_id === id);
}

export function families(): string[] {
  return [...new Set(data.scenarios.map((item) => item.family))];
}

export function measuredModels(): MeasuredTrial[] {
  return data.models as MeasuredTrial[];
}

export function measuredTrials(scenario: Scenario): MeasuredTrial[] {
  return scenario.measured_trials as MeasuredTrial[];
}
