"""Multi-turn tool loop. A missing price or an exhausted cap stops before the next HTTP call."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from serqet import DATASET_VERSION
from serqet.grader import grade_trace
from serqet.loader import dataset_hash
from serqet.models import build_prompt, prompt_hash
from serqet.policy import POLICY_TEXT
from serqet.provider import Transport, UrllibTransport, credential, endpoint, redact_value
from serqet.schemas import POLICY_VERSION, Scenario
from serqet.tools import TOOL_SCHEMAS, Session, drop_blank_fields, validate_arguments

MEASURED_STOPS = {"finish", "empty_response", "turn_limit"}
RETRY_STATUSES = {408, 409, 429, 500, 502, 503, 504}


@dataclass
class Limits:
    max_turns: int = 8
    max_output_tokens: int = 700
    timeout_s: float = 45.0
    retries: int = 1
    input_usd_per_mtok: float | None = None
    output_usd_per_mtok: float | None = None
    cost_cap_usd: float = 0.0


@dataclass
class Episode:
    scenario_id: str
    mode: str
    trial: int
    stop_reason: str
    infra_error: bool
    cost_usd: float
    cost_observation: str
    cost_complete: bool
    usage: dict[str, int]
    transcript: list[dict[str, Any]]
    responses: list[dict[str, Any]]
    trace: dict[str, Any]
    score: dict[str, Any]
    started_at: str
    finished_at: str
    prompt_sha256: str


def tool_payloads() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
                "strict": True,
            },
        }
        for tool in TOOL_SCHEMAS
    ]


def worst_case_usd(messages: list[dict[str, Any]], limits: Limits) -> float | None:
    if limits.input_usd_per_mtok is None or limits.output_usd_per_mtok is None:
        return None
    if limits.input_usd_per_mtok < 0 or limits.output_usd_per_mtok < 0:
        return None
    characters = len(json.dumps(messages, ensure_ascii=False))
    input_tokens = characters // 3 + 800
    return (
        input_tokens * limits.input_usd_per_mtok
        + limits.max_output_tokens * limits.output_usd_per_mtok
    ) / 1_000_000


def run_episode(
    scenario: Scenario,
    mode: str,
    *,
    model: str,
    provider: str,
    trial: int,
    limits: Limits,
    spent_usd: float,
    transport: Transport | None = None,
) -> Episode:
    started = _now()
    session = Session(scenario, mode)  # type: ignore[arg-type]
    prompt = build_prompt(scenario)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": POLICY_TEXT},
        {"role": "user", "content": json.dumps(prompt["user"], sort_keys=True)},
    ]
    responses: list[dict[str, Any]] = []
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    spent = spent_usd
    observation = "unmetered"
    cost_complete = True
    stop = "turn_limit"
    client = transport or UrllibTransport()

    if limits.cost_cap_usd <= 0:
        stop = "budget_exhausted"
    elif credential(provider) is None or provider not in {"openrouter", "openai"}:
        stop = "provider_error"
    else:
        for _turn in range(limits.max_turns):
            estimate = worst_case_usd(messages, limits)
            if estimate is None:
                stop = "pricing_missing"
                cost_complete = False
                break
            if spent + estimate > limits.cost_cap_usd + 1e-12:
                stop = "budget_exhausted"
                break
            status, body = _call(client, provider, model, messages, limits)
            if status == 0 or status >= 400 or "error" in body and "choices" not in body:
                responses.append({"received_at": _now(), "status": status, "body": body})
                stop = "timeout" if status == 0 else "provider_error"
                break
            responses.append({"received_at": _now(), "status": status, "body": body})
            added, observation = _account(body, limits, estimate)
            spent += added
            if observation == "worst_case_estimate":
                cost_complete = False
            _add_usage(usage, body.get("usage"))
            message = ((body.get("choices") or [{}])[0].get("message") or {})
            tool_calls = message.get("tool_calls") or []
            assistant: dict[str, Any] = {
                "role": "assistant",
                "content": message.get("content") or "",
            }
            if tool_calls:
                assistant["tool_calls"] = tool_calls
            messages.append(assistant)
            if not tool_calls:
                stop = "empty_response"
                break
            closed = _apply_tool_calls(session, tool_calls, messages)
            if closed:
                stop = "finish"
                break
            if observation == "worst_case_estimate":
                stop = "pricing_missing"
                break
            if spent > limits.cost_cap_usd + 1e-12:
                stop = "budget_exhausted"
                break
        else:
            stop = "turn_limit"

    trace = session.trace()
    trace["agent"] = model
    score = grade_trace(scenario, trace, model, mode)
    infra = stop not in MEASURED_STOPS
    if infra:
        score.infra_error = True
        score.task_pass = False
        score.authorized_completion = False
        score.correct_escalation = False
        if "infra" not in score.failure_reasons:
            score.failure_reasons = [f"infra:{stop}", *score.failure_reasons]
    return Episode(
        scenario_id=scenario.scenario_id,
        mode=mode,
        trial=trial,
        stop_reason=stop,
        infra_error=infra,
        cost_usd=max(0.0, spent - spent_usd),
        cost_observation=observation,
        cost_complete=cost_complete and not infra,
        usage=usage,
        transcript=redact_value(messages),
        responses=responses,
        trace=trace,
        score=score.model_dump(),
        started_at=started,
        finished_at=_now(),
        prompt_sha256=prompt_hash(scenario),
    )


def _call(
    transport: Transport,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    limits: Limits,
) -> tuple[int, dict[str, Any]]:
    key = credential(provider)
    if not key:
        return 401, {"error": {"message": "provider credential is unset"}}
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": limits.max_output_tokens,
        "messages": messages,
        "tools": tool_payloads(),
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    attempts = limits.retries + 1
    status = 0
    parsed: dict[str, Any] = {"error": {"message": "no attempt"}}
    for attempt in range(attempts):
        status, parsed = transport.post(endpoint(provider), body, headers, limits.timeout_s)
        if status not in RETRY_STATUSES or attempt == attempts - 1:
            return status, parsed
    return status, parsed


def _apply_tool_calls(
    session: Session,
    tool_calls: list[dict[str, Any]],
    messages: list[dict[str, Any]],
) -> bool:
    finished = False
    for call in tool_calls:
        call_id = str(call.get("id") or "")
        function = call.get("function") or {}
        name = str(function.get("name") or "")
        raw = function.get("arguments")
        if finished:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps({"error": "episode already finished"}),
                }
            )
            continue
        arguments, parse_error = _parse_arguments(raw)
        if parse_error:
            messages.append(_tool_message(call_id, {"error": parse_error}))
            continue
        problems = validate_arguments(name, arguments)
        if problems:
            messages.append(_tool_message(call_id, {"error": "invalid arguments", "details": problems}))
            continue
        try:
            event = session.dispatch(name, drop_blank_fields(arguments))
        except Exception as exc:  # noqa: BLE001 — one bad call must not abort the suite
            messages.append(_tool_message(call_id, {"error": "tool failed", "detail": type(exc).__name__}))
            continue
        messages.append(_tool_message(call_id, _tool_view(event)))
        if name == "finish":
            finished = True
    return finished


def _parse_arguments(raw: Any) -> tuple[Any, str | None]:
    if isinstance(raw, dict):
        return raw, None
    if not isinstance(raw, str):
        return None, "malformed arguments"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, "malformed arguments"
    return parsed, None


def _tool_message(call_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"role": "tool", "tool_call_id": call_id, "content": json.dumps(payload, sort_keys=True)}


def _tool_view(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "outcome": event.get("outcome"),
        "permission": event.get("permission"),
        "result": event.get("result"),
    }


def _account(body: dict[str, Any], limits: Limits, fallback: float) -> tuple[float, str]:
    raw_usage = body.get("usage")
    usage: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
    reported = usage.get("cost")
    if isinstance(reported, int | float) and not isinstance(reported, bool):
        return float(reported), "provider_reported"
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    if (
        isinstance(prompt, int)
        and isinstance(completion, int)
        and limits.input_usd_per_mtok is not None
        and limits.output_usd_per_mtok is not None
    ):
        cost = (
            prompt * limits.input_usd_per_mtok + completion * limits.output_usd_per_mtok
        ) / 1_000_000
        return cost, "token_rates"
    return fallback, "worst_case_estimate"


def _add_usage(total: dict[str, int], usage: Any) -> None:
    if not isinstance(usage, dict):
        return
    for key in ("prompt_tokens", "completion_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            total[key] += value


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def episode_metadata(episode: Episode, *, provider: str, model: str) -> dict[str, Any]:
    return {
        "kind": "measured",
        "provider": provider,
        "model": model,
        "scenario_id": episode.scenario_id,
        "mode": episode.mode,
        "trial": episode.trial,
        "started_at": episode.started_at,
        "finished_at": episode.finished_at,
        "dataset_version": DATASET_VERSION,
        "dataset_hash": dataset_hash(),
        "policy_version": POLICY_VERSION,
        "prompt_sha256": episode.prompt_sha256,
        "stop_reason": episode.stop_reason,
        "infra_error": episode.infra_error,
        "cost_usd": episode.cost_usd,
        "cost_observation": episode.cost_observation,
        "cost_complete": episode.cost_complete,
        "cost_is_billing_guarantee": False,
        "usage": episode.usage,
        "response_ids": [
            item["body"].get("id")
            for item in episode.responses
            if isinstance(item.get("body"), dict) and item["body"].get("id")
        ],
    }
