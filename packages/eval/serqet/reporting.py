"""Summaries for the CLI, the submission ZIP, and the dashboard."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from serqet import DATASET_VERSION
from serqet.baselines import BASELINES, oracle_agent
from serqet.grader import grade_trace, run_agent
from serqet.loader import dataset_hash, load_scenarios
from serqet.sandbox import Sandbox
from serqet.schemas import POLICY_VERSION, TaskScore
from serqet.suite import MODES, run_controls

FAMILY_LABELS = {
    "patient_context": "Patient context",
    "consent_toctou": "Consent revocation",
    "approval_toctou": "Approval withdrawal",
    "delegation": "Delegated scope",
    "forged_authority": "Forged authority",
}


def ratio(matches: int, total: int) -> dict[str, float | int | None]:
    return {
        "numerator": matches,
        "denominator": total,
        "rate": None if total == 0 else matches / total,
    }


def metric_block(scores: list[TaskScore]) -> dict[str, Any]:
    positives = [item for item in scores if item.polarity == "positive"]
    negatives = [item for item in scores if item.polarity == "negative"]

    def count(items: list[TaskScore], field: str) -> dict[str, float | int | None]:
        return ratio(sum(1 for item in items if getattr(item, field)), len(items))

    return {
        "task_pass": count(scores, "task_pass"),
        "authorized_completion_rate": count(positives, "authorized_completion"),
        "unauthorized_attempt_rate": count(scores, "unauthorized_attempt"),
        "unauthorized_effect_rate": count(scores, "unauthorized_effect"),
        "correct_escalation_rate": count(negatives, "correct_escalation"),
        "false_refusal_rate": count(positives, "false_refusal"),
        "false_success_claim_rate": count(scores, "false_success_claim"),
        "audit_provenance_integrity_rate": count(scores, "audit_provenance_ok"),
        "tool_calls": sum(item.tool_calls for item in scores),
        "infra_errors": sum(1 for item in scores if item.infra_error),
    }


def control_matrix(scores: list[TaskScore]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[TaskScore]]] = defaultdict(lambda: defaultdict(list))
    for item in scores:
        grouped[item.agent][item.mode].append(item)
    rendered: dict[str, Any] = {}
    for agent, modes in grouped.items():
        rendered[agent] = {}
        for mode, items in modes.items():
            rendered[agent][mode] = {
                "passed": sum(1 for item in items if item.task_pass),
                "total": len(items),
                "metrics": metric_block(items),
                "tasks": [item.model_dump() for item in items],
            }
    return rendered


def demo_traces() -> dict[str, Any]:
    demos: dict[str, Any] = {}
    for scenario in load_scenarios():
        trace = run_agent(scenario, "oracle_agent", "shadow", oracle_agent)
        score = grade_trace(scenario, trace, "oracle_agent", "shadow")
        demos[scenario.scenario_id] = {
            "kind": "simulated_demo",
            "not_model_results": True,
            "label": "SIMULATED DEMO",
            "agent": "oracle_agent",
            "mode": "shadow",
            "events": [_public_event(event) for event in trace["events"]],
            "score": score.model_dump(),
            "final_hash": trace["final_hash"],
        }
    return demos


def public_bundle(scores: list[TaskScore] | None = None) -> dict[str, Any]:
    if scores is None:
        scores = run_controls()
    demos = demo_traces()
    scenarios = []
    for scenario in load_scenarios():
        sandbox = Sandbox(scenario)
        scenarios.append(
            {
                "scenario_id": scenario.scenario_id,
                "family": scenario.family,
                "family_label": FAMILY_LABELS.get(scenario.family, scenario.family),
                "polarity": scenario.polarity,
                "seed": scenario.seed,
                "difficulty": scenario.difficulty,
                "title": scenario.title,
                "summary": scenario.summary,
                "user_task": scenario.agent_visible.user_task,
                "normative_rule": scenario.grader_private.normative_rule,
                "identity": scenario.agent_visible.identity.model_dump(),
                "requested_operation": scenario.agent_visible.requested_operation.as_action(),
                "schedule": [item.model_dump() for item in scenario.grader_private.schedule],
                "resources": _resource_list(sandbox.snapshot()),
                "approvals": list(sandbox.snapshot()["approvals"].values()),
                "model_status": "not_measured",
                "demo": demos[scenario.scenario_id],
            }
        )
    return {
        "dataset_version": DATASET_VERSION,
        "dataset_hash": dataset_hash(),
        "policy_version": POLICY_VERSION,
        "measurement_status": "NOT_MEASURED",
        "measurement_note": (
            "No model API was called. Rows under controls are scripted reference agents, "
            "not frontier-model results. Oracle replays are simulated demos."
        ),
        "models": [],
        "scenarios": scenarios,
        "controls": control_matrix(scores),
        "agents": list(BASELINES),
        "modes": list(MODES),
    }


def _resource_list(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for grouped in snapshot["fhir"].values():
        rows.extend(grouped.values())
    rows.sort(key=lambda item: (item["resourceType"], item["id"]))
    return rows


def _public_event(event: dict[str, Any]) -> dict[str, Any]:
    result = event["result"]
    preview = result
    if isinstance(result, dict) and "resource" in result and isinstance(result["resource"], dict):
        resource = result["resource"]
        preview = {
            **{key: value for key, value in result.items() if key != "resource"},
            "resource_type": resource.get("resourceType"),
            "resource_id": resource.get("id"),
            "description": resource.get("description"),
            "status": resource.get("status"),
        }
    return {
        "step": event["step"],
        "logical_time": event["logical_time"],
        "actor": event["actor"],
        "tool": event["tool"],
        "outcome": event["outcome"],
        "permission": event["permission"],
        "request": event["request"],
        "result": preview,
    }


def write_json(path: Any, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
