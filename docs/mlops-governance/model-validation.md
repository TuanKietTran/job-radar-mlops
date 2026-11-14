# Model validation

## Purpose

Independent check that a model is fit for its stated purpose, before production use and on a schedule after that.

## Independence

The validator is not the developer and not the owner of the model. The validator reports findings to the approver, not to the developer. A validator who helped build the model does not validate it.

## When validation happens

- Before first production use.
- After any change to inputs, outputs, thresholds, or training data that changes results.
- On the review schedule: Tier 1 every 6 months, Tier 2 every 12 months, Tier 3 every 24 months.
- After a drift alert that was not resolved by retraining on the same data. See runbooks/runbook-drift.md.

## What validation checks

- Conceptual soundness: purpose, inputs, and limits are written down and match the inventory entry.
- Data: sources are recorded with versions, quality checks pass, and no personal data sits outside the fields named in the inventory.
- Performance: metrics on holdout data are recorded, compared with the previous version, and inside the thresholds named in the inventory.
- Stability: results do not change materially when inputs vary inside the recorded ranges.
- Fairness: outcomes are checked across the groups named in the inventory. Gaps are recorded even when small.
- Overfitting: training and holdout metrics are compared. A gap above the recorded limit is a finding.
- Implementation: the served version matches the validated version, the code path is reviewed, and a rollback step exists.

## Findings

- Critical: blocks production use until closed.
- Major: must close before approval, or the approver accepts it in writing with an expiry date.
- Minor: recorded with a fix date. Production use can proceed while the fix is open.

## Validation report

Every validation produces a report that records model id and version, data versions, metrics, the checks run, findings with severity, the outcome, the validator role, and the date. The outcome is one of Pass, Pass with conditions, or Fail.

## After a Fail

A model that fails stays out of production. The developer records the fix, the validator re-runs the failed checks, and the report records both the first outcome and the re-run. A model that fails twice in a row goes back to the approver before any further production request.

## Records

Validation reports are kept under the retention rules in audit-trail.md and are readable by the auditor without developer help.
