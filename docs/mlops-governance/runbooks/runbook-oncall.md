# Runbook: on-call

## Purpose

Give the responder on duty a fixed order of work for any production model incident: confirm, contain, record, escalate, and hand over.

## Roles on duty

- On-call responder: first to act, confirms the incident and runs the first checks.
- Model owner: decides the response and owns the record for their model.
- Model developer: investigates and prepares a retrain, a fix, or a rollback.
- Approver: decides on rollback or suspension where approval-workflow.md requires it.
- Auditor: reads the incident record after the fact. The auditor is not on call.

Roles are recorded as roles, not as persons. The handover names the role, not only the person holding it.

## Severity

- Severity 1: a Tier 1 model produces wrong decisions, or any model serves a version that does not match its validated version. First response within 30 minutes.
- Severity 2: a Tier 2 model produces wrong decisions, or a drift alert stays outside its threshold after retraining. First response within 2 hours.
- Severity 3: a Tier 3 model produces wrong decisions, or a monitoring check fails with no wrong decisions yet. First response within one working day.

Severity is set by the responder at first contact and reviewed by the owner. A severity is raised when the impact grows, never lowered while the impact is unknown.

## Steps

1. Confirm. Record the model id, model version, the symptom, the time the symptom started, and the severity. Check the inventory entry in docs/mlops-governance/model-inventory.md and confirm the served version matches the validated version.
2. Contain. Stop the harm first. For a wrong-decision incident, suspend the model under approval-workflow.md. For a version mismatch, follow runbooks/runbook-rollback.md. Containment comes before diagnosis.
3. Notify. Tell the model owner at once for Severity 1 and Severity 2, and within one working day for Severity 3. Tell the approver on the same day for a Tier 1 suspension or rollback.
4. Diagnose. The developer investigates with the validator where the cause is unclear. Record each check and its result. A cause is recorded only when the evidence names it. An unknown cause is recorded as unknown.
5. Decide the fix. The owner picks one: rollback under runbooks/runbook-rollback.md, retrain under runbooks/runbook-retrain.md, a data fix followed by validation, or retirement. A fix that alters inputs, outputs, or thresholds is a new version and restarts approval under approval-workflow.md.
6. Record. Log every step in the audit trail under docs/mlops-governance/audit-trail.md: the incident, the severity, the containment step, the cause, the fix, and the roles involved. A record with a missing field is incomplete and is flagged for the auditor.
7. Verify. Confirm the fix with the checks recorded in the validation report for the version now serving. Resume serving only after the served version check and the smoke check pass.
8. Review. Within 5 working days, the owner and the responder review the incident: what happened, how long each step took, and what changes. The review is recorded with a date and the roles present. A review that finds a repeated cause opens a fix with a date and a role.

## Handover

At the end of a shift, the outgoing responder hands over open incidents in writing: model id, severity, current state, next step, and the time of the next check. An incident with no written handover is still open and stays with the outgoing responder until the handover is recorded.

## After an incident

Re-run the maturity assessment when the incident changes a score, for example when monitoring or governance failed to catch the issue:

```
python3 mlops/maturity/assess.py --answers mlops/maturity/examples/baseline-answers.json --out docs/mlops-governance/reports/baseline
```

Replace the answers file with the current answers for the model when the assessment is run for a real review. Record the total score in the incident review.

## What not to do

- Do not diagnose before containing a wrong-decision incident.
- Do not lower a severity while the impact is unknown.
- Do not close an incident with an unknown cause and no next check date.
- Do not hand over an open incident verbally.
