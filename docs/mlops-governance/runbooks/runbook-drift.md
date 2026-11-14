# Runbook: drift

## Purpose

Respond to a drift alert on a production model: confirm the alert, decide the response, and record it.

## Trigger

A drift alert fires when a monitored metric passes the threshold named in the model inventory entry. The metrics and thresholds are the ones recorded at validation in model-validation.md. An alert is not a fix on its own. It starts this runbook.

## Roles

- On-call responder: confirms the alert and runs the first checks.
- Model owner: decides the response and owns the record.
- Model developer: investigates the cause and prepares a retrain or a fix.
- Approver: signs off on a rollback or a suspension where approval-workflow.md requires it.

## Steps

1. Confirm the alert. Record the model id, model version, metric, threshold, observed value, and the date and time. Check that the alert names a model with an inventory entry in docs/mlops-governance/model-inventory.md. An alert for a model with no entry is reported to the owner and the auditor as a gap, and the model is suspended until the entry exists.
2. Check the served version. Confirm the served version matches the validated version in the inventory entry. A mismatch is not drift. Follow runbooks/runbook-rollback.md to restore the validated version, and record the mismatch in the audit trail.
3. Check the data version. Confirm the input data version matches the version named in the inventory entry. A data version change without a recorded validation restarts validation under model-validation.md before any other step.
4. Compare current metrics with the validation report. Use the metrics recorded at validation as the baseline. Record the size of the change and whether the change is in the inputs, the outputs, or both.
5. Check for a known cause. Look for a recent release, a data source change, or a seasonal pattern recorded in earlier drift alerts for the same model. Record the cause when found, and record that no cause was found when the checks are empty.
6. Decide the response with the owner. The options are: keep monitoring with a shorter check interval, retrain under runbooks/runbook-retrain.md, roll back under runbooks/runbook-rollback.md, or suspend the model under approval-workflow.md. A drift alert that is not resolved by retraining on the same data triggers validation again under model-validation.md.
7. Record the decision. Log the alert, the checks, the decision, and the role that made it in the audit trail under docs/mlops-governance/audit-trail.md. The record names the next check date.
8. Close the alert or escalate. Close it only when the metric returns inside its threshold for the period named in the inventory entry, or when a retrain, rollback, or suspension has replaced it. Escalate to the approver when the metric stays outside its threshold after retraining, or when the drift affects a Tier 1 model.

## After the response

Re-run the maturity assessment to confirm the monitoring and governance scores still hold:

```
python3 mlops/maturity/assess.py --answers mlops/maturity/examples/baseline-answers.json --out docs/mlops-governance/reports/baseline
```

Replace the answers file with the current answers for the model when the assessment is run for a real review. The output is score.json and report.html in the output directory. Record the total score and the monitoring dimension score in the drift record.

## What not to do

- Do not change a threshold to clear an alert. A threshold change is a model change and restarts validation.
- Do not retrain on new data without recording the new training data version in the inventory entry.
- Do not leave an alert open with no next check date.
