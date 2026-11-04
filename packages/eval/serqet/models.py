"""Prompt construction and the optional provider boundary.

Live HTTP calls happen only after a positive cost cap and a provider key.
The default cap is zero, so `verify` and `--dry-run` never open a socket.
"""

from __future__ import annotations

import hashlib
from typing import Any

from serqet.canon import canonical
from serqet.policy import POLICY_TEXT
from serqet.provider import credential
from serqet.schemas import Scenario
from serqet.tools import TOOL_SCHEMAS


def build_prompt(scenario: Scenario) -> dict[str, Any]:
    """Return the model-facing prompt. Grader fields are not included."""
    return {
        "system": POLICY_TEXT,
        "user": {
            "task": scenario.agent_visible.user_task,
            "identity": scenario.agent_visible.identity.model_dump(),
            "requested_operation": scenario.agent_visible.requested_operation.as_action(),
        },
        "tools": TOOL_SCHEMAS,
    }


def prompt_hash(scenario: Scenario) -> str:
    return hashlib.sha256(canonical(build_prompt(scenario)).encode("utf-8")).hexdigest()


def provider_key() -> str | None:
    """OpenRouter credential only. An OpenAI key is not sent to OpenRouter."""
    return credential("openrouter")


def dry_run_manifest(model: str, trials: int) -> dict[str, Any]:
    from serqet.loader import load_scenarios

    return {
        "kind": "dry_run",
        "not_model_results": True,
        "model": model,
        "trials": trials,
        "network": False,
        "prompts": [
            {"scenario_id": scenario.scenario_id, "prompt_sha256": prompt_hash(scenario)}
            for scenario in load_scenarios()
        ],
    }


def live_chat(
    *,
    model: str,
    scenario: Scenario,
    cost_cap_usd: float,
    timeout_s: float = 60,
) -> dict[str, Any]:
    """Refuse a one-shot call. Evaluation goes through the multi-turn harness."""
    del model, scenario, timeout_s
    if cost_cap_usd <= 0:
        raise RuntimeError("cost cap is 0; refusing the provider call")
    if not credential("openrouter"):
        raise RuntimeError("OPENROUTER_API_KEY is unset; refusing the provider call")
    raise RuntimeError("use serqet run-models; live_chat does not send a one-shot request")
