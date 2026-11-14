# Model inventory

One entry per model. A model with no entry here is not in production. All example entries use invented names and synthetic data.

## Template

Copy this block for a new model and fill every field. Leave no field blank. Write `none` where a field does not apply.

| Field | Entry |
| --- | --- |
| Model id |  |
| Model name |  |
| Version |  |
| Risk tier |  |
| Owner role |  |
| Developer role |  |
| Purpose |  |
| Data sources |  |
| Training data version |  |
| Metrics |  |
| Validation date |  |
| Validation outcome |  |
| Approval date |  |
| Approver role |  |
| Status |  |
| Review due |  |
| Retirement date |  |

## Example 1: job match ranker

| Field | Entry |
| --- | --- |
| Model id | MOD-001 |
| Model name | job-match-ranker |
| Version | 1.2.0 |
| Risk tier | Tier 2 |
| Owner role | Search Owner |
| Developer role | Ranking Developer |
| Purpose | Rank synthetic job listings for a search query by relevance |
| Data sources | Synthetic listings set v3, synthetic interaction log v2 |
| Training data version | listings-synth-v3 |
| Metrics | Precision at 10: 0.62 on synthetic holdout, set 2026-11-01 |
| Validation date | 2026-11-05 |
| Validation outcome | Pass with two findings, both closed |
| Approval date | 2026-11-07 |
| Approver role | Model Risk Approver |
| Status | Production |
| Review due | 2027-05-07 |
| Retirement date | none |

## Example 2: income estimator for lending pre-screen

| Field | Entry |
| --- | --- |
| Model id | MOD-002 |
| Model name | income-estimator |
| Version | 0.9.1 |
| Risk tier | Tier 1 |
| Owner role | Credit Analytics Owner |
| Developer role | Credit Modelling Developer |
| Purpose | Estimate applicant income band from synthetic application fields for pre-screen triage |
| Data sources | Synthetic application set v1, synthetic bureau extract v1 |
| Training data version | applications-synth-v1 |
| Metrics | Mean absolute error: 3.4 million VND on synthetic holdout, set 2026-11-01 |
| Validation date | 2026-11-06 |
| Validation outcome | Pass with one condition, monitoring threshold tightened |
| Approval date | 2026-11-08 |
| Approver role | Model Risk Approver |
| Status | Production |
| Review due | 2027-02-08 |
| Retirement date | none |

## Rules

- Model ids are assigned in order and never reused, including after retirement.
- The owner role is a role, not a person. When the person in the role changes, the entry keeps the role and the audit trail records the handover.
- A version change that alters inputs, outputs, or thresholds is a new inventory entry, not an edit to the old one.
- Status is one of: Development, Staging, Production, Suspended, Retired.
- Review due is set at approval: Tier 1 every 6 months, Tier 2 every 12 months, Tier 3 every 24 months.
