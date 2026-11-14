# Model card: salary-v1-1.0.0

## Intended use

Estimates a monthly salary in VND for a synthetic job posting and ranks postings for a fixed reference profile (target skills python, sql, aws, docker; preferred cities Ha Noi and Ho Chi Minh; preferred levels middle and senior).
Built for offline evaluation of the job aggregator on synthetic data only. Not used to set pay, screen candidates, or make hiring decisions.

## Metrics

- Held-out set size: 500
- MAE: 2010420.36 VND
- RMSE: 2546783.78 VND
- Precision at 10: 1.0
- NDCG at 10: 1.0

## Fairness

- Max MAE gap across slices: 444976.49 VND
- Max selection-rate gap across slices: 0.2938
- Drift PSI, true vs predicted salary bands: 0.0197
- Flags: 2
  - city selection gap 0.2938 over cap 0.2
  - industry selection gap 0.2502 over cap 0.2

## Limitations

- Trained and evaluated on synthetic data only; figures do not describe the real job market.
- Linear formula on experience, city, industry and level; it misses skill mix, company size and negotiation.
- Salary bands are coarse (four bands) and relevance grades come from one fixed reference profile.
- Predictions are monthly VND estimates, not offers and not a substitute for market data.

## Approval

Not approved: one or more gates failed.
