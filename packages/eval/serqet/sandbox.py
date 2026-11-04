"""Resettable in-memory store. FHIR resources and the two non-FHIR ledgers are separate."""

from __future__ import annotations

import copy
from datetime import timedelta
from typing import Any

from serqet.canon import canonical, format_instant, logical_time, parse_instant, sha256_hex
from serqet.fixtures import default_approvals, hospital_resources, validate_r4_subset
from serqet.schemas import POLICY_VERSION, Scenario

DIRECTORY_TYPES = {"Practitioner", "PractitionerRole", "Organization"}


class Sandbox:
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.fhir = hospital_resources()
        self.approvals = default_approvals()
        self.disclosures: list[dict[str, Any]] = []
        self.step = 0
        for consent_id, status in scenario.world.consent_status.items():
            self._set_consent(consent_id, status, bump=False)
        for approval_id, status in scenario.world.approval_status.items():
            self._set_approval(approval_id, status, bump=False)
        for grouped in self.fhir.values():
            for resource in grouped.values():
                validate_r4_subset(resource)

    def logical_now(self) -> str:
        return logical_time(self.step)

    def snapshot(self) -> dict[str, Any]:
        return {
            "fhir": copy.deepcopy(self.fhir),
            "approvals": copy.deepcopy(self.approvals),
            "disclosures": copy.deepcopy(self.disclosures),
        }

    def state_hash(self) -> str:
        return sha256_hex(canonical(self.snapshot()))

    def get(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        found = self.fhir.get(resource_type, {}).get(resource_id)
        return copy.deepcopy(found) if found is not None else None

    def approval(self, approval_id: str) -> dict[str, Any] | None:
        row = self.approvals.get(approval_id)
        return copy.deepcopy(row) if row is not None else None

    def _live(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        try:
            return self.fhir[resource_type][resource_id]
        except KeyError as exc:
            raise KeyError(f"{resource_type}/{resource_id}") from exc

    def _bump(self, resource: dict[str, Any]) -> None:
        current = int(resource["meta"]["versionId"])
        resource["meta"]["versionId"] = str(current + 1)

    def _set_consent(self, consent_id: str, status: str, *, bump: bool) -> None:
        resource = self._live("Consent", consent_id)
        resource["status"] = status
        if bump:
            self._bump(resource)
        validate_r4_subset(resource)

    def _set_approval(self, approval_id: str, status: str, *, bump: bool) -> None:
        row = self.approvals[approval_id]
        row["status"] = status
        if bump:
            row["version"] = int(row["version"]) + 1

    def apply_schedule_item(self, item: Any) -> str:
        if item.set_consent_status is not None:
            self._set_consent(
                item.set_consent_status.id,
                item.set_consent_status.status,
                bump=True,
            )
            return f"Consent/{item.set_consent_status.id}"
        if item.set_approval_status is not None:
            self._set_approval(
                item.set_approval_status.id,
                item.set_approval_status.status,
                bump=True,
            )
            return f"ApprovalLedger/{item.set_approval_status.id}"
        raise ValueError("schedule item has no mutation")

    def reschedule(self, appointment_id: str, new_start: str) -> str:
        resource = self._live("Appointment", appointment_id)
        start = parse_instant(new_start)
        resource["start"] = format_instant(start)
        resource["end"] = format_instant(start + timedelta(minutes=20))
        self._bump(resource)
        validate_r4_subset(resource)
        return f"Appointment/{appointment_id}"

    def book(self, appointment_id: str) -> str:
        resource = self._live("Appointment", appointment_id)
        resource["status"] = "booked"
        self._bump(resource)
        validate_r4_subset(resource)
        return f"Appointment/{appointment_id}"

    def record_disclosure(
        self,
        *,
        scenario_id: str,
        patient_id: str,
        observation_id: str,
        consent_id: str,
        purpose: str,
        recipient: str,
        step: int,
    ) -> str:
        consent = self._live("Consent", consent_id)
        disclosure_id = f"disc-{scenario_id}-{step}"
        self.disclosures.append(
            {
                "record_type": "DisclosureLedger",
                "id": disclosure_id,
                "patient_id": patient_id,
                "observation_id": observation_id,
                "consent_id": consent_id,
                "consent_version": str(consent["meta"]["versionId"]),
                "purpose": purpose,
                "recipient": recipient,
                "status": "recorded",
            }
        )
        return f"Observation/{observation_id}"

    def write_audit(
        self,
        *,
        step: int,
        action: str,
        reference: str,
        outcome: str,
        principal_id: str,
        purpose: str,
        outcome_class: str,
    ) -> None:
        resource_id = f"aud-{step}-{outcome_class}"
        resource = {
            "resourceType": "AuditEvent",
            "id": resource_id,
            "meta": {"versionId": "1"},
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
                "code": "rest",
            },
            "action": action,
            "recorded": self.logical_now(),
            "outcome": outcome,
            "outcomeDesc": outcome_class,
            "purposeOfEvent": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                            "code": purpose,
                        }
                    ]
                }
            ],
            "agent": [
                {
                    "who": {"reference": f"Practitioner/{principal_id}"},
                    "requestor": True,
                }
            ],
            "source": {"observer": {"reference": "Organization/org-khepri"}},
            "entity": [
                {
                    "what": {"reference": reference},
                    "description": f"step={step};class={outcome_class}",
                }
            ],
        }
        validate_r4_subset(resource)
        self.fhir.setdefault("AuditEvent", {})[resource_id] = resource

    def write_environment_audit(self, *, step: int, reference: str, reason: str) -> None:
        resource_id = f"aud-env-{step}"
        resource = {
            "resourceType": "AuditEvent",
            "id": resource_id,
            "meta": {"versionId": "1"},
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
                "code": "rest",
            },
            "action": "U",
            "recorded": self.logical_now(),
            "outcome": "0",
            "outcomeDesc": "environment",
            "agent": [
                {
                    "who": {"reference": "Organization/org-khepri"},
                    "requestor": True,
                }
            ],
            "source": {"observer": {"reference": "Organization/org-khepri"}},
            "entity": [
                {
                    "what": {"reference": reference},
                    "description": f"step={step};class=environment;reason={reason}",
                }
            ],
        }
        validate_r4_subset(resource)
        self.fhir.setdefault("AuditEvent", {})[resource_id] = resource

    def write_provenance(self, *, step: int, reference: str, principal_id: str) -> None:
        resource_id = f"prov-{step}"
        resource = {
            "resourceType": "Provenance",
            "id": resource_id,
            "meta": {"versionId": "1"},
            "target": [{"reference": reference}],
            "recorded": self.logical_now(),
            "policy": [f"urn:serqet:policy:{POLICY_VERSION}", f"urn:serqet:step:{step}"],
            "activity": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                        "code": "UPDATE",
                    }
                ]
            },
            "agent": [{"who": {"reference": f"Practitioner/{principal_id}"}}],
        }
        validate_r4_subset(resource)
        self.fhir.setdefault("Provenance", {})[resource_id] = resource
