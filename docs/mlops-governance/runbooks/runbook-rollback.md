# Runbook: rollback

## Purpose

Return a production model to the previous validated version after a bad release, a failed validation, or a drift alert that retraining did not resolve.

## When to roll back

- The served version does not match the validated version in the inventory entry.
- A new version produces wrong decisions and the cause is not a data version change.
- A drift alert stays outside its threshold after retraining on the same data.
- The approver or the owner orders a rollback after a failed review.

## Roles

- Model owner: orders the rollback and owns the record.
- Model developer: restores the previous version and verifies the served version.
- Approver: signs off where approval-workflow.md requires it. Tier 1 rollbacks are reported to the approver on the same day.
- Auditor: reads the rollback record. The auditor does not run the rollback.

## Preconditions

- The previous version has an inventory entry in docs/mlops-governance/model-inventory.md with a recorded validation outcome of Pass or Pass with conditions.
- The previous version, its training data version, and its thresholds are recorded. A version with no validation record is not a rollback target.
- The rollback step for the model was recorded at approval. If no rollback step exists, the owner records one before the rollback and the approver signs it.

## Steps

1. Record the decision. Log the model id, the version rolled back from, the version rolled back to, the reason, the date and time, and the role that ordered it. The record goes in the audit trail under docs/mlops-governance/audit-trail.md.
2. Suspend the current version. Stop the current version from serving new decisions. Decisions already recorded stay in the audit trail and are not changed.
3. Restore the previous version. Serve the previous validated version with its recorded thresholds and its recorded training data version. Do not merge settings from the failed version into the restored version.
4. Verify the served version. Confirm the served version, the data version, and the thresholds match the inventory entry for the restored version. A mismatch stops the rollout and the model stays suspended.
5. Run a smoke check. Run the checks recorded in the validation report for the restored version and confirm the metrics are inside their thresholds. Record the check result with the date.
6. Resume serving. Resume only after step 4 and step 5 pass. Record the resume date and time in the audit trail.
7. Notify. Tell the owner, the validator, and the approver that the rollback is complete, with the model id, both versions, and the reason. Tier 1 rollbacks are reported to the approver on the same day.
8. Follow up. The failed version goes back to Gate 1 of approval-workflow.md before any further production request. A model that fails twice in a row goes back to the approver before any further production request, as stated in model-validation.md.

## After the rollback

Re-run the maturity assessment to confirm the serving and governance scores still hold:

```
python3 mlops/maturity/assess.py --answers mlops/maturity/examples/baseline-answers.json --out docs/mlops-governance/reports/baseline
```

Replace the answers file with the current answers for the model when the assessment is run for a real review. Record the total score in the rollback record.

## What not to do

- Do not roll back to a version with no validation record.
- Do not edit the failed version in place and call it a rollback. A rollback restores a recorded version.
- Do not resume serving before the served version check passes.
