# Data provenance

Every patient, practitioner, and organization in the sandbox was written for this benchmark. Names (Noah Pell, Noah Peller, Lina Vasquez, Imani Adeyemi, Samir Okonkwo, Elena Cho, Ada Pell) and identifiers (`pat-river-noah-pell`, and the rest in `fixtures.py`) are fictional. The identifier system is `https://khepri.example/synthetic`.

No EIR fixture file was copied. No real hospital extract, no real MRN, and no public case report was used as a chart.

Observations use LOINC `29463-7` (body weight) with round kilogram values. The tasks tell the agent to file or read the record, not to interpret it. Appointments are administrative slots. The care plan text says it is not a treatment order. Consents use R4 `status`, `scope` `patient-privacy`, category `research`, and a provision limited to one observation for purpose `HRESCH`.

`ApprovalLedger` and `DisclosureLedger` are labeled with `record_type` and are not given a FHIR `resourceType`.

The local checker in `validate_r4_subset` rejects a resource that lacks the fields this suite depends on, including R4 required elements for `AuditEvent` and `Provenance`. It does not claim FHIR publication conformance.

Logical time is derived from a fixed epoch plus the tool step. Re-running the controls does not depend on the wall clock.
