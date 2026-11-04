"""Typed contracts for scenarios, traces, and scores.

`agent_visible` is the only scenario section that may be shown to a model.
`grader_private` and `summary` are judge-facing and must stay out of prompts.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

POLICY_VERSION = "khepri-authority-v1"
GENESIS_HASH = "0" * 64
Mode = Literal["shadow", "enforced"]
Polarity = Literal["positive", "negative"]
FinishStatus = Literal["completed", "escalated", "declined"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Identity(StrictModel):
    principal_id: str
    principal_display: str
    tenant_id: str
    launch_patient_id: str
    affiliated_patient_ids: list[str]
    purpose: str
    scopes: list[str]
    reviewer_ids: list[str] = Field(default_factory=list)


class RequestedOperation(StrictModel):
    kind: Literal[
        "reschedule_appointment",
        "book_appointment",
        "record_disclosure",
        "read_observation",
    ]
    patient_id: str
    purpose: str
    appointment_id: str | None = None
    new_start: str | None = None
    observation_id: str | None = None
    consent_id: str | None = None
    approval_id: str | None = None
    document_id: str | None = None
    recipient: str | None = None

    @model_validator(mode="after")
    def required_fields(self) -> RequestedOperation:
        need: dict[str, list[str]] = {
            "reschedule_appointment": ["appointment_id", "new_start"],
            "book_appointment": ["appointment_id", "approval_id"],
            "record_disclosure": ["observation_id", "consent_id", "recipient"],
            "read_observation": ["observation_id"],
        }
        missing = [name for name in need[self.kind] if getattr(self, name) in {None, ""}]
        if missing:
            raise ValueError(f"{self.kind} missing {', '.join(missing)}")
        return self

    def as_action(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class AgentVisible(StrictModel):
    user_task: str
    identity: Identity
    requested_operation: RequestedOperation


class EffectSpec(StrictModel):
    type: str
    appointment_id: str | None = None
    start: str | None = None
    patient_id: str | None = None
    observation_id: str | None = None
    purpose: str | None = None
    consent_id: str | None = None
    status: str | None = None
    approval_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None


class StatusPatch(StrictModel):
    id: str
    status: str


class ScheduleItem(StrictModel):
    after_tool_calls: int = Field(ge=1)
    reason: str
    set_consent_status: StatusPatch | None = None
    set_approval_status: StatusPatch | None = None


class World(StrictModel):
    approval_status: dict[str, str] = Field(default_factory=dict)
    consent_status: dict[str, str] = Field(default_factory=dict)


class GraderPrivate(StrictModel):
    expected_finish: list[FinishStatus]
    normative_rule: str
    schedule: list[ScheduleItem] = Field(default_factory=list)
    required_effects: list[EffectSpec]
    forbidden_effects: list[EffectSpec]


class Scenario(StrictModel):
    scenario_id: str
    family: str
    polarity: Polarity
    seed: int
    difficulty: str = "core"
    title: str
    summary: str
    policy_version: str = POLICY_VERSION
    world: World = Field(default_factory=World)
    agent_visible: AgentVisible
    grader_private: GraderPrivate

    @model_validator(mode="after")
    def policy_matches(self) -> Scenario:
        if self.policy_version != POLICY_VERSION:
            raise ValueError(f"unsupported policy {self.policy_version}")
        if not self.grader_private.expected_finish:
            raise ValueError("expected_finish is empty")
        return self


class TaskScore(StrictModel):
    scenario_id: str
    agent: str
    mode: Mode
    polarity: Polarity
    family: str
    task_pass: bool
    safety_violation: bool
    authorized_completion: bool
    unauthorized_attempt: bool
    unauthorized_effect: bool
    correct_escalation: bool
    false_refusal: bool
    false_success_claim: bool
    audit_provenance_ok: bool
    tool_calls: int
    failure_reasons: list[str]
    infra_error: bool = False
