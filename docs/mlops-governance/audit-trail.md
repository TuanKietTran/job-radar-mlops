# Audit trail

## Purpose

The audit trail records what happened to each model, when it happened, and who was responsible, so that any production decision can be traced to a model version, a data version, and an input record.

## What is logged

The following events are logged for every model. An event with a missing field is incomplete and is recorded as a gap for the auditor.

- Inventory change: model id, version, field changed, previous value, new value, date, role.
- Validation: model id, version, data versions, metrics, findings with severity, outcome, validator role, date.
- Approval: model id, version, decision, conditions and expiry dates, approver role, second approver role where required, date.
- Release: model id, version, release date, served version, monitoring start date, role.
- Production decision: model id, version, input record reference, output, date. The input record is referenced by id, not copied in full where the source system holds it.
- Drift alert: model id, version, metric, threshold, observed value, date, response taken. See runbooks/runbook-drift.md.
- Retrain: model id, previous version, new version, training data version, metrics, date, role. See runbooks/runbook-retrain.md.
- Rollback: model id, version rolled back from, version rolled back to, reason, date, role. See runbooks/runbook-rollback.md.
- Suspension and restart: model id, version, reason, date, role that ordered the change.
- Retirement: model id, version, retirement date, reason, role.
- Exception: model id, request date, expiry date, approver role, date.
- Access to audit records: role, date, records read. Access by the auditor is logged in the same way as any other access.

## Record format

Each event records the date and time, the model id, the event type, the role responsible, and the fields listed above. Records use plain text and readable field names. A record that depends on a file elsewhere names the file and its version.

## Storage and integrity

Audit records are stored apart from the model code and the model data, so that a change to a model cannot change its own audit record. Records are append only. A correction is a new record that names the record it corrects. Deletion of audit records is not permitted during the retention period.

## Access

The auditor reads audit records without developer help. The owner, the validator, and the approver read the records for their own models. Access is limited to the roles named in model-risk-policy.md. No role outside that list reads audit records.

## Retention

- Inventory entries, validation reports, approval records, release records, and retirement records: kept for 7 years after the model is retired.
- Production decision records: kept for 7 years after the decision date.
- Drift alerts, retrain records, rollback records, and suspension records: kept for 7 years after the event date.
- Audit access records: kept for 3 years after the access date.

Retention is counted from the latest date named in each line above. After the retention period ends, records are removed under a recorded disposal step that names the model id, the record type, and the date of disposal.

## Review

The auditor checks the trail once a year and after any material incident. The check covers completeness of the events listed above, missing fields, gaps in dates, and records that name a model with no inventory entry. Findings from the check are recorded with a fix date and the role responsible for the fix.
