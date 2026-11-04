"""Mocked provider loop, budget stops, and measured-record integrity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from serqet.budget import BudgetError, BudgetLedger
from serqet.harness import Limits, run_episode, tool_payloads, worst_case_usd
from serqet.integrity import apply_trials, collect_trials, validate_trial, write_episode
from serqet.loader import load_scenarios
from serqet.provider import credential, endpoint
from serqet.reporting import public_bundle
from serqet.tools import ACTION_SCHEMA, validate_arguments

MODEL = "openrouter/test-model"


class FakeTransport:
    def __init__(self, responses: list[tuple[int, dict[str, Any]]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        body: bytes,
        headers: dict[str, str],
        timeout: float,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {"url": url, "body": json.loads(body), "timeout": timeout, "has_auth": "Authorization" in headers}
        )
        return self.responses.pop(0)


def _scenario(scenario_id: str):
    return next(item for item in load_scenarios() if item.scenario_id == scenario_id)


def _action(scenario_id: str) -> dict[str, str]:
    scenario = _scenario(scenario_id)
    action = {key: "" for key in ACTION_SCHEMA["required"]}
    action.update(scenario.agent_visible.requested_operation.as_action())
    return action


def _call(name: str, arguments: dict[str, Any], ident: str) -> dict[str, Any]:
    return {
        "id": ident,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def _completion(
    ident: str,
    tool_calls: list[dict[str, Any]] | None = None,
    content: str = "",
) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {
        "id": ident,
        "model": MODEL,
        "created": 1762220000,
        "choices": [
            {
                "message": message,
                "finish_reason": "tool_calls" if tool_calls else "stop",
            }
        ],
        "usage": {"prompt_tokens": 80, "completion_tokens": 20, "cost": 0.0001},
    }


def _limits(**overrides: float | int | None) -> Limits:
    values: dict[str, float | int | None] = {
        "max_turns": 4,
        "max_output_tokens": 200,
        "timeout_s": 5,
        "retries": 1,
        "input_usd_per_mtok": 1.0,
        "output_usd_per_mtok": 1.0,
        "cost_cap_usd": 1.0,
    }
    values.update(overrides)
    return Limits(**values)  # type: ignore[arg-type]


def test_tool_schema_rejects_unknown_fields() -> None:
    names = [item["function"]["name"] for item in tool_payloads()]
    assert "execute_action" in names
    assert "finish" in names
    bad = _action("deleg-ward-read")
    bad["note"] = "ignore policy"
    assert validate_arguments("check_authorization", {"action": bad})
    assert validate_arguments("missing_tool", {}) == ["unknown tool missing_tool"]


def test_multi_turn_preserves_tool_call_ids(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-credential")
    scenario = _scenario("ctx-reschedule-adjacent")
    first = _call("check_authorization", {"action": _action(scenario.scenario_id)}, "call-check")
    second = _call(
        "finish",
        {"status": "escalated", "claim": "launch patient does not match"},
        "call-finish",
    )
    transport = FakeTransport(
        [
            (200, _completion("resp-1", [first])),
            (200, _completion("resp-2", [second])),
        ]
    )
    episode = run_episode(
        scenario,
        "enforced",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(),
        spent_usd=0,
        transport=transport,
    )
    assert episode.stop_reason == "finish"
    assert episode.score["task_pass"] is True
    assert transport.calls[0]["url"] == endpoint("openrouter")
    follow_up = transport.calls[1]["body"]["messages"]
    tool_messages = [item for item in follow_up if item["role"] == "tool"]
    assert tool_messages[0]["tool_call_id"] == "call-check"
    assert "permit" in tool_messages[0]["content"]
    directory = tmp_path / "trial"
    write_episode(directory, episode, provider="openrouter", model=MODEL)
    ok, reason = validate_trial(directory)
    assert ok, reason
    saved = directory.read_text() if directory.is_file() else "\n".join(
        path.read_text(encoding="utf-8") for path in directory.iterdir()
    )
    assert "unit-test-credential" not in saved
    assert transport.calls[0]["has_auth"] is True


def test_malformed_unknown_and_empty_do_not_crash_the_suite(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-credential")
    scenario = _scenario("deleg-ward-read")
    malformed = {
        "id": "call-bad",
        "type": "function",
        "function": {"name": "read_resource", "arguments": "{"},
    }
    unknown = _call("drop_table", {"query": "patients"}, "call-unknown")
    finish = _call("finish", {"status": "declined", "claim": "stopping"}, "call-finish")
    transport = FakeTransport(
        [
            (200, _completion("resp-bad", [malformed, unknown])),
            (200, _completion("resp-finish", [finish])),
        ]
    )
    episode = run_episode(
        scenario,
        "enforced",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(),
        spent_usd=0,
        transport=transport,
    )
    assert episode.stop_reason == "finish"
    blob = json.dumps(episode.transcript)
    assert "malformed arguments" in blob
    assert "unknown tool drop_table" in blob
    assert all(event["tool"] == "finish" for event in episode.trace["events"])

    empty = FakeTransport([(200, _completion("resp-empty", content=""))])
    quiet = run_episode(
        scenario,
        "enforced",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(),
        spent_usd=0,
        transport=empty,
    )
    assert quiet.stop_reason == "empty_response"
    assert quiet.infra_error is False


def test_budget_pricing_and_provider_errors_do_not_become_model_failures(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-credential")
    scenario = _scenario("deleg-ward-read")
    blocked = FakeTransport([(200, _completion("should-not-send"))])
    episode = run_episode(
        scenario,
        "shadow",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(cost_cap_usd=0.0000001),
        spent_usd=0,
        transport=blocked,
    )
    assert episode.stop_reason == "budget_exhausted"
    assert blocked.calls == []
    assert episode.infra_error is True

    unpriced = run_episode(
        scenario,
        "shadow",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(input_usd_per_mtok=None, output_usd_per_mtok=None),
        spent_usd=0,
        transport=blocked,
    )
    assert unpriced.stop_reason == "pricing_missing"
    assert blocked.calls == []

    failing = FakeTransport(
        [
            (500, {"error": {"message": "upstream"}}),
            (500, {"error": {"message": "upstream"}}),
        ]
    )
    failed = run_episode(
        scenario,
        "shadow",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(),
        spent_usd=0,
        transport=failing,
    )
    assert failed.stop_reason == "provider_error"
    assert len(failing.calls) == 2
    directory = tmp_path / "failed"
    write_episode(directory, failed, provider="openrouter", model=MODEL)
    ok, reason = validate_trial(directory)
    assert not ok
    assert "not a model result" in reason


def test_retry_after_rate_limit_then_records_a_measured_turn(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-credential")
    scenario = _scenario("ctx-reschedule-adjacent")
    finish = _call("finish", {"status": "declined", "claim": "no"}, "call-finish")
    transport = FakeTransport(
        [
            (429, {"error": {"message": "rate limit"}}),
            (200, _completion("resp-ok", [finish])),
        ]
    )
    episode = run_episode(
        scenario,
        "enforced",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(),
        spent_usd=0,
        transport=transport,
    )
    assert len(transport.calls) == 2
    assert episode.stop_reason == "finish"
    assert episode.score["task_pass"] is True


def test_openai_key_is_not_a_credential_for_openrouter(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-unit-value")
    assert credential("openrouter") is None
    assert credential("openai") == "openai-unit-value"
    assert "openrouter.ai" in endpoint("openrouter")
    assert "api.openai.com" in endpoint("openai")


def test_metadata_alone_cannot_mark_a_report_measured(tmp_path) -> None:
    fake = tmp_path / "only-meta"
    fake.mkdir()
    (fake / "metadata.json").write_text(json.dumps({"kind": "measured", "model": "invented"}), encoding="utf-8")
    accepted, rejected = collect_trials(tmp_path)
    assert accepted == []
    assert rejected
    bundle = {"measurement_status": "NOT_MEASURED", "models": [], "scenarios": []}
    assert apply_trials(bundle, accepted)["measurement_status"] == "NOT_MEASURED"


def test_report_command_rejects_a_fabricated_measured_flag(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "measured"
    source.mkdir()
    (source / "metadata.json").write_text(json.dumps({"kind": "measured"}), encoding="utf-8")
    from serqet.cli import main

    output = tmp_path / "summary.json"
    # public_bundle reads the repo scenarios, not the cwd.
    code = main(["report", "--input", str(source), "--output", str(output)])
    assert code == 2
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["measurement_status"] == "NOT_MEASURED"
    assert written["models"] == []


def test_public_bundle_keeps_controls_when_no_valid_trials() -> None:
    bundle = public_bundle()
    assert bundle["measurement_status"] == "NOT_MEASURED"
    assert bundle["scenarios"][0]["measured_trials"] == []
    assert bundle["controls"]["oracle_agent"]["shadow"]["passed"] == 10


def test_shared_ledger_stops_a_second_five_dollar_cap(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-credential")
    first = BudgetLedger(tmp_path / "ledger.json", ceiling_usd=0.05, absolute_usd=0.05)
    second = BudgetLedger(tmp_path / "ledger.json", ceiling_usd=0.05, absolute_usd=0.05)
    held = first.authorize(0.04)
    assert held is not None
    assert second.authorize(0.04) is None
    first.settle(held, 0.04)
    assert second.authorize(0.02) is None
    assert abs(second.remaining_usd - 0.01) < 1e-9
    scenario = _scenario("deleg-ward-read")
    blocked = FakeTransport([(200, _completion("should-not-send"))])
    episode = run_episode(
        scenario,
        "shadow",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(cost_cap_usd=5),
        spent_usd=0,
        transport=blocked,
        ledger=BudgetLedger(tmp_path / "tiny.json", ceiling_usd=1e-9, absolute_usd=1e-6),
    )
    assert episode.stop_reason == "budget_exhausted"
    assert blocked.calls == []
    estimate = worst_case_usd(
        [{"role": "user", "content": "x"}],
        _limits(cost_cap_usd=5),
    )
    assert estimate is not None and estimate > 1e-9


def test_provider_rejection_releases_the_reservation_and_timeout_holds_it(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-credential")
    scenario = _scenario("deleg-ward-read")
    rejected = BudgetLedger(tmp_path / "reject.json", ceiling_usd=1, absolute_usd=1)
    failure = FakeTransport([(400, {"error": {"message": "strict tools rejected"}})])
    episode = run_episode(
        scenario,
        "shadow",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(retries=0),
        spent_usd=0,
        transport=failure,
        ledger=rejected,
    )
    assert episode.stop_reason == "provider_error"
    assert rejected.spent_usd == 0
    assert rejected.remaining_usd == 1
    timed_out = BudgetLedger(tmp_path / "timeout.json", ceiling_usd=1, absolute_usd=1)
    outage = FakeTransport([(0, {"error": {"message": "timeout"}})])
    stalled = run_episode(
        scenario,
        "shadow",
        model=MODEL,
        provider="openrouter",
        trial=1,
        limits=_limits(retries=0),
        spent_usd=0,
        transport=outage,
        ledger=timed_out,
    )
    assert stalled.stop_reason == "timeout"
    assert timed_out.spent_usd > 0


def test_ledger_refuses_a_ceiling_above_five_dollars(tmp_path) -> None:
    try:
        BudgetLedger(tmp_path / "high.json", ceiling_usd=6, absolute_usd=6)
    except BudgetError as exc:
        assert "authorized" in str(exc)
    else:
        raise AssertionError("ceiling above 5 USD was accepted")


def test_changed_score_and_model_id_are_rejected(tmp_path) -> None:
    repo = Path(__file__).resolve().parents[3]
    source = next((repo / "artifacts" / "measured").rglob("metadata.json")).parent
    destination = tmp_path / "trial"
    destination.mkdir()
    for name in ("metadata.json", "transcript.json", "events.json", "score.json", "responses.json"):
        (destination / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")
    score_path = destination / "score.json"
    score = json.loads(score_path.read_text(encoding="utf-8"))
    score["task_pass"] = not score["task_pass"]
    score_path.write_text(json.dumps(score), encoding="utf-8")
    ok, reason = validate_trial(destination)
    assert not ok
    assert "score" in reason
    score["task_pass"] = not score["task_pass"]
    score_path.write_text(json.dumps(score), encoding="utf-8")
    metadata_path = destination / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["model"] = "replaced/model"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    ok, reason = validate_trial(destination)
    assert not ok
    assert "model" in reason
