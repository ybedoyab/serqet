"""Prompt construction and the optional provider boundary.

Live HTTP calls happen only after a positive cost cap and a provider key.
The default cap is zero, so `verify` and `--dry-run` never open a socket.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from urllib import request as urlrequest

from serqet.canon import canonical
from serqet.policy import POLICY_TEXT
from serqet.schemas import Scenario
from serqet.tools import TOOL_SCHEMAS

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


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
    for name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    return None


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
    """Place one OpenAI-compatible chat call. Callers must gate this themselves."""
    if cost_cap_usd <= 0:
        raise RuntimeError("cost cap is 0; refusing the provider call")
    key = provider_key()
    if not key:
        raise RuntimeError("provider key is unset; refusing the provider call")
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": POLICY_TEXT},
            {"role": "user", "content": json.dumps(build_prompt(scenario)["user"])},
        ],
        "tools": [
            {"type": "function", "function": {"name": tool["name"], "parameters": tool["parameters"]}}
            for tool in TOOL_SCHEMAS
        ],
    }
    req = urlrequest.Request(
        OPENROUTER_URL,
        data=canonical(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=timeout_s) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))
