# Approval workflow

## Purpose

This document sets the gates a model passes before production use, who signs at each gate, and what record the sign-off leaves. No model moves to production on a verbal approval.

## Roles

- Model owner: accountable for the model, its inventory entry, and its review schedule. Requests approval and owns the production decision.
- Model developer: builds and documents the model, supplies training data, code, metrics, and the rollback step. Does not approve the model.
- Validator: independent of the developer and the owner. Checks the model against model-validation.md and records findings. Does not approve the model.
- Approver: a senior role that signs off or rejects. The approver is not the developer and not the validator for the same model.
- Second approver: required for Tier 1 only. A senior role separate from the first approver.
- Auditor: reads the approval record and checks that it is complete. Does not approve.

Roles are recorded as roles, not as persons. When the person in a role changes, the record keeps the role and the audit trail records the handover.

## Gates

### Gate 0: intake

The owner creates or updates the inventory entry in model-inventory.md with model id, version, risk tier, purpose, data sources, and metrics. A model with no inventory entry does not proceed.

The owner confirms the risk tier against model-risk-policy.md. A tier change after validation restarts the workflow at Gate 1.

### Gate 1: validation

The validator runs the checks in model-validation.md and issues a report with outcome Pass, Pass with conditions, or Fail.

- Pass: the model proceeds to Gate 2.
- Pass with conditions: each condition is recorded with a fix date. The approver decides whether production use can start before the fix date.
- Fail: the model stops. The developer records the fix, the validator re-runs the failed checks, and the report records both outcomes. A model that fails twice in a row goes back to the approver before any further production request.

Critical findings block Gate 2 until closed. Major findings close before approval, or the approver accepts them in writing with an expiry date.

### Gate 2: approval

The owner submits the inventory entry, the validation report, and the rollback step to the approver.

- Tier 1: first approver and second approver both sign. Either may reject.
- Tier 2: one approver signs.
- Tier 3: one approver signs.

The approver records one of three decisions: Approve, Approve with conditions, or Reject. A rejection records the reason and the change required before resubmission. An approval with conditions records each condition and its expiry date.

### Gate 3: production release

After approval, the owner records the release date, the served version, and the monitoring start date in the inventory entry. The served version must match the validated version. A mismatch returns the model to Gate 1.

### Gate 4: periodic review

Review follows the schedule in model-validation.md: Tier 1 every 6 months, Tier 2 every 12 months, Tier 3 every 24 months. A review that finds the model no longer fit for purpose suspends production use until Gate 1 and Gate 2 run again.

## Sign-off record

Every approval records the following fields. A record with a missing field is not an approval.

| Field | Entry |
| --- | --- |
| Model id |  |
| Model version |  |
| Risk tier |  |
| Validation report date |  |
| Validation outcome |  |
| Findings open at approval |  |
| Conditions and expiry dates |  |
| Approver role |  |
| Second approver role |  |
| Decision |  |
| Decision date |  |
| Next review due |  |

## Changes after approval

A change to inputs, outputs, thresholds, or training data that changes results is a new version and restarts the workflow at Gate 1. A change that does not alter results is recorded in the inventory entry with the date and the reason, and does not restart the workflow.

## Exceptions

An exception needs a written request, a named expiry date, and approver sign-off. An exception without an expiry date is not valid. An exception does not remove the model from the inventory or from the review schedule.

## Emergency suspension

The owner or the approver can suspend a production model at any time when it produces wrong decisions. Suspension is recorded with the date, the reason, and the role that ordered it. Restarting a suspended model requires Gate 1 and Gate 2 again.
