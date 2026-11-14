# Model risk policy

## Purpose

This policy sets how models used by the bank are identified, tiered, validated, approved, and retired. It covers every model that affects a lending decision, a price, a limit, a fraud check, or a customer message.

## Scope

This policy applies to all models in production and staging, and to retired models kept for audit. It applies to models built in house and to models bought from a vendor. It also applies to scripts used as models when they drive a decision recorded in the audit trail.

## Principles

- One owner per model, named in the inventory.
- No production model without a validation record and a recorded approval.
- Risk tier decides the depth of review, not the team that built the model.
- Every decision a model influences can be traced to a model version, a data version, and an input record.
- Models are reviewed on a schedule, not only after an incident.

## Risk tiers

- Tier 1, high: a model whose error can cause direct financial loss to a customer or the bank, or a wrong regulatory report.
- Tier 2, medium: a model whose error can cause wrong routing, wrong prioritisation, or a degraded service.
- Tier 3, low: a model whose error is visible, reversible, and limited to internal reporting.

## Roles

- Model owner: accountable for the model, its inventory entry, and its review schedule.
- Model developer: builds and documents the model, and hands over training data, code, and metrics.
- Validator: independent of the developer, checks the model against this policy and records findings.
- Approver: a senior role named in approval-workflow.md, signs off or rejects.
- Auditor: reads the audit trail and checks that records are complete.

## Inventory

Every model has one entry in model-inventory.md. A model with no entry is not in production.

## Validation

Validation is independent, documented in model-validation.md, and repeated on the schedule in that document. A validation that fails blocks production use until the finding is closed or the approver accepts the risk in writing.

## Approval

Approval follows approval-workflow.md. No model moves to production on a verbal approval.

## Monitoring and drift

Production models are monitored for drift and performance as described in runbooks/runbook-drift.md. A drift alert starts a recorded response, not an informal fix.

## Audit and retention

Audit records follow audit-trail.md. Records are kept for the retention period in that document and are readable by the auditor without developer help.

## Exceptions

An exception needs a written request, a named expiry date, and approver sign-off. An exception without an expiry date is not valid.

## Review of this policy

This policy is reviewed once a year and after any material incident. Changes are recorded with a date and a version.
