"""Measured-run integrity. A `kind: measured` flag is not evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from serqet import DATASET_VERSION
from serqet.grader import grade_trace
from serqet.harness import MEASURED_STOPS, Episode, episode_metadata
from serqet.loader import dataset_hash, load_scenarios
from serqet.models import prompt_hash
from serqet.provider import redact
from serqet.reporting import public_event, ratio
from serqet.schemas import POLICY_VERSION

REQUIRED_FILES = (
    "metadata.json",
    "transcript.json",
    "events.json",
    "score.json",
    "responses.json",
)
SECRET_MARKERS = ("Bearer ", "sk-", "OPENROUTER_API_KEY=", "OPENAI_API_KEY=")


def write_episode(directory: Path, episode: Episode, *, provider: str, model: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    _dump(directory / "metadata.json", episode_metadata(episode, provider=provider, model=model))
    _dump(directory / "transcript.json", {"messages": episode.transcript})
    _dump(
        directory / "events.json",
        {
            "events": episode.trace["events"],
            "final_hash": episode.trace["final_hash"],
            "finish_status": episode.trace["finish_status"],
            "finish_claim": episode.trace["finish_claim"],
            "mode": episode.mode,
        },
    )
    _dump(directory / "score.json", episode.score)
    _dump(directory / "responses.json", {"responses": episode.responses})


def collect_trials(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[str] = []
    if not root.exists():
        return accepted, rejected
    for meta_path in sorted(root.rglob("metadata.json")):
        ok, reason = validate_trial(meta_path.parent)
        if ok:
            accepted.append(public_trial(meta_path.parent))
        else:
            rejected.append(f"{meta_path.parent.as_posix()}: {reason}")
    return accepted, rejected


def validate_trial(directory: Path) -> tuple[bool, str]:
    for name in REQUIRED_FILES:
        if not (directory / name).is_file():
            return False, f"missing {name}"
    blob = "\n".join((directory / name).read_text(encoding="utf-8") for name in REQUIRED_FILES)
    if any(marker in blob for marker in SECRET_MARKERS):
        return False, "secret marker"
    try:
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        transcript = json.loads((directory / "transcript.json").read_text(encoding="utf-8"))
        events_doc = json.loads((directory / "events.json").read_text(encoding="utf-8"))
        score = json.loads((directory / "score.json").read_text(encoding="utf-8"))
        responses = json.loads((directory / "responses.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, "invalid json"
    if metadata.get("kind") == "measured" and set(metadata) == {"kind"}:
        return False, "kind alone is not evidence"
    required = [
        "provider",
        "model",
        "scenario_id",
        "mode",
        "trial",
        "started_at",
        "finished_at",
        "dataset_version",
        "dataset_hash",
        "policy_version",
        "prompt_sha256",
        "stop_reason",
        "cost_usd",
        "cost_observation",
        "cost_complete",
        "cost_is_billing_guarantee",
        "usage",
        "response_ids",
        "infra_error",
    ]
    missing = [name for name in required if name not in metadata]
    if missing:
        return False, "metadata missing " + ",".join(missing)
    if metadata["stop_reason"] not in MEASURED_STOPS or metadata["infra_error"] is not False:
        return False, "provider or budget failure is not a model result"
    if metadata["cost_complete"] is not True or metadata["cost_is_billing_guarantee"] is not False:
        return False, "cost evidence is incomplete"
    if metadata["cost_observation"] not in {"provider_reported", "token_rates"}:
        return False, "cost was not observed"
    if metadata["dataset_version"] != DATASET_VERSION or metadata["dataset_hash"] != dataset_hash():
        return False, "dataset mismatch"
    if metadata["policy_version"] != POLICY_VERSION:
        return False, "policy mismatch"
    if not metadata["model"] or not metadata["started_at"] or not metadata["finished_at"]:
        return False, "model or timestamp missing"
    scenario = next(
        (item for item in load_scenarios() if item.scenario_id == metadata["scenario_id"]),
        None,
    )
    if scenario is None:
        return False, "unknown scenario"
    if metadata["prompt_sha256"] != prompt_hash(scenario):
        return False, "prompt mismatch"
    bodies = responses.get("responses")
    if not isinstance(bodies, list) or not bodies:
        return False, "no provider response"
    seen_ids: list[str] = []
    for item in bodies:
        body = item.get("body") if isinstance(item, dict) else None
        if not isinstance(body, dict) or not item.get("received_at"):
            return False, "response envelope incomplete"
        if not body.get("id") or not body.get("model") or not body.get("choices"):
            return False, "response is missing id, model, or choices"
        if body["model"] != metadata["model"]:
            return False, "response model does not match metadata"
        seen_ids.append(str(body["id"]))
    if metadata["response_ids"] != seen_ids:
        return False, "response id mismatch"
    messages = transcript.get("messages")
    if not isinstance(messages, list) or not messages:
        return False, "transcript missing"
    if not _transcript_ids_match(messages):
        return False, "tool call id missing from transcript"
    trace = {
        "scenario_id": metadata["scenario_id"],
        "agent": metadata["model"],
        "mode": metadata["mode"],
        "events": events_doc.get("events"),
        "final_hash": events_doc.get("final_hash"),
        "final_state": {},
        "finish_status": events_doc.get("finish_status"),
        "finish_claim": events_doc.get("finish_claim"),
    }
    if not isinstance(trace["events"], list):
        return False, "events missing"
    fresh = grade_trace(scenario, trace, metadata["model"], metadata["mode"])
    if fresh.model_dump() != score:
        return False, "score does not match replay"
    if redact(json.dumps(metadata)) != json.dumps(metadata):
        return False, "metadata needs redaction"
    return True, ""


def public_trial(directory: Path) -> dict[str, Any]:
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    events_doc = json.loads((directory / "events.json").read_text(encoding="utf-8"))
    score = json.loads((directory / "score.json").read_text(encoding="utf-8"))
    return {
        "label": "MEASURED MODEL RESULT",
        "provider": metadata["provider"],
        "model": metadata["model"],
        "started_at": metadata["started_at"],
        "finished_at": metadata["finished_at"],
        "scenario_id": metadata["scenario_id"],
        "mode": metadata["mode"],
        "trial": metadata["trial"],
        "dataset_version": metadata["dataset_version"],
        "policy_version": metadata["policy_version"],
        "stop_reason": metadata["stop_reason"],
        "cost_usd": metadata["cost_usd"],
        "cost_observation": metadata["cost_observation"],
        "cost_is_billing_guarantee": False,
        "usage": metadata["usage"],
        "task_pass": score["task_pass"],
        "failure_reasons": score["failure_reasons"],
        "unauthorized_attempt": score["unauthorized_attempt"],
        "unauthorized_effect": score["unauthorized_effect"],
        "authorized_completion": score["authorized_completion"],
        "correct_escalation": score["correct_escalation"],
        "false_refusal": score["false_refusal"],
        "false_success_claim": score["false_success_claim"],
        "events": [public_event(event) for event in events_doc["events"]],
    }


def apply_trials(bundle: dict[str, Any], trials: list[dict[str, Any]]) -> dict[str, Any]:
    if not trials:
        return bundle
    updated = json.loads(json.dumps(bundle))
    updated["measurement_status"] = "MEASURED"
    updated["measurement_note"] = (
        "Measured rows are provider responses graded by the sandbox. "
        "Reference controls and simulated demos are separate. "
        "The cost cap is an estimate, not a billing guarantee."
    )
    updated["models"] = trials
    updated["measured_metrics"] = _metrics(trials)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trial in trials:
        grouped.setdefault(trial["scenario_id"], []).append(trial)
    for scenario in updated["scenarios"]:
        rows = grouped.get(scenario["scenario_id"], [])
        scenario["measured_trials"] = rows
        scenario["model_status"] = "measured" if rows else "not_measured"
    return updated


def _metrics(trials: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trial in trials:
        grouped.setdefault(f"{trial['provider']}/{trial['model']}/{trial['mode']}", []).append(trial)
    rendered: dict[str, Any] = {}
    for key, rows in grouped.items():
        positives = [item for item in rows if _polarity(item) == "positive"]
        negatives = [item for item in rows if _polarity(item) == "negative"]

        def count(items: list[dict[str, Any]], field: str) -> dict[str, float | int | None]:
            return ratio(sum(1 for item in items if item[field]), len(items))

        rendered[key] = {
            "trials": len(rows),
            "task_pass": count(rows, "task_pass"),
            "authorized_completion_rate": count(positives, "authorized_completion"),
            "unauthorized_attempt_rate": count(rows, "unauthorized_attempt"),
            "unauthorized_effect_rate": count(rows, "unauthorized_effect"),
            "correct_escalation_rate": count(negatives, "correct_escalation"),
            "false_refusal_rate": count(positives, "false_refusal"),
            "false_success_claim_rate": count(rows, "false_success_claim"),
            "cost_usd": sum(float(item["cost_usd"]) for item in rows),
        }
    return rendered


def _polarity(trial: dict[str, Any]) -> str:
    scenario = next(item for item in load_scenarios() if item.scenario_id == trial["scenario_id"])
    return scenario.polarity


def _transcript_ids_match(messages: list[dict[str, Any]]) -> bool:
    answered = {
        message.get("tool_call_id")
        for message in messages
        if message.get("role") == "tool" and message.get("tool_call_id")
    }
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            if call.get("id") not in answered:
                return False
    return True


def _dump(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
