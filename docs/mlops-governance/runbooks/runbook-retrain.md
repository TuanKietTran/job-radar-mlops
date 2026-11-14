# Runbook: retrain

## Purpose

Retrain a production model on new data, or on the same data after a drift alert, and return it to production through validation and approval.

## When to retrain

- A drift alert names a data change that a retrain can address. See runbooks/runbook-drift.md.
- The review schedule in model-validation.md is due and the data has changed since the last training run.
- The owner orders a retrain after a performance check shows metrics outside their thresholds.

Retraining on the same data after a drift alert that it did not resolve triggers validation again under model-validation.md. Retraining on new data always triggers validation and approval.

## Roles

- Model owner: orders the retrain and owns the inventory entry.
- Model developer: runs the training, records the data version and metrics, and hands over the new version.
- Validator: validates the new version under model-validation.md. The validator is not the developer.
- Approver: signs off under approval-workflow.md before the new version serves production traffic.

## Steps

1. Freeze the training data. Record the training data version and the data sources in the inventory entry in docs/mlops-governance/model-inventory.md before training starts. A retrain with no recorded training data version does not proceed.
2. Record the new version. Assign a new model version in the inventory entry. A version change that alters inputs, outputs, or thresholds is a new entry, not an edit to the old one.
3. Train. The developer runs the training and records the metrics on holdout data, the comparison with the previous version, and the training and holdout gap. The served version is not changed during training.
4. Validate. The validator runs the checks in model-validation.md on the new version and issues a report with outcome Pass, Pass with conditions, or Fail. A Fail stops the retrain. The developer records the fix, the validator re-runs the failed checks, and the report records both outcomes.
5. Approve. The owner submits the inventory entry, the validation report, and the rollback step to the approver under approval-workflow.md. Tier 1 needs two approvers. No verbal approval moves a model to production.
6. Release. After approval, record the release date, the served version, and the monitoring start date in the inventory entry. The served version must match the validated version. Follow runbooks/runbook-rollback.md when it does not.
7. Monitor. Watch the metrics named in the inventory entry for the period recorded at validation. A drift alert in that period starts runbooks/runbook-drift.md.
8. Record. Log the retrain in the audit trail under docs/mlops-governance/audit-trail.md: model id, previous version, new version, training data version, metrics, date, and role.

## After the retrain

Re-run the maturity assessment to confirm the training and governance scores still hold:

```
python3 mlops/maturity/assess.py --answers mlops/maturity/examples/baseline-answers.json --out docs/mlops-governance/reports/baseline
```

Replace the answers file with the current answers for the model when the assessment is run for a real review. Record the total score and the training dimension score in the retrain record.

## What not to do

- Do not train on data with no recorded version.
- Do not serve the new version before approval.
- Do not reuse the old version number for a model trained on new data.
- Do not skip the holdout comparison with the previous version.
