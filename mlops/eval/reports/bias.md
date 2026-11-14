# Bias and fairness report: salary-v1-1.0.0

Held-out set size: 500. Median predicted salary: 30750000.0 VND.

Group attributes are city, industry and employment_type, the only group attributes in the synthetic data. The data carries no protected attributes, so no protected-label analysis is possible here; do not read these job-posting slices as protected groups.

Thresholds: disparate impact ratio >= 0.8; demographic parity difference <= 0.2; equal opportunity difference <= 0.2.
Selection is predicted salary at or above the median; ranking selection is inclusion in the top 10 by rank score.
Equal opportunity uses true high pay (salary band 3 or 4) for salary and relevance grade >= 2 for ranking.

## city

| group | n | selection rate | top-10 rate | TPR salary | TPR ranking |
| --- | --- | --- | --- | --- | --- |
| Cần Thơ | 55 | 0.3273 | 0.0 | 1.0 | 0.0 |
| Hà Nội | 144 | 0.5 | 0.0278 | 1.0 | 0.0412 |
| Hải Phòng | 50 | 0.32 | 0.0 | 1.0 | 0.0 |
| Hồ Chí Minh | 189 | 0.6138 | 0.0317 | 1.0 | 0.0408 |
| Đà Nẵng | 62 | 0.4839 | 0.0 | 1.0 | 0.0 |

- Disparate impact ratio: 0.5213
- Demographic parity difference: 0.2938
- Equal opportunity difference (salary): 0.0
- Equal opportunity difference (ranking): 0.0412

## industry

| group | n | selection rate | top-10 rate | TPR salary | TPR ranking |
| --- | --- | --- | --- | --- | --- |
| Banking | 102 | 0.4314 | 0.0392 | 1.0 | 0.069 |
| IT Software | 225 | 0.5911 | 0.0133 | 1.0 | 0.0217 |
| Logistics | 44 | 0.3409 | 0.0 | 1.0 | 0.0 |
| Manufacturing | 69 | 0.4493 | 0.029 | 1.0 | 0.0488 |
| Retail | 60 | 0.4833 | 0.0167 | 1.0 | 0.0294 |

- Disparate impact ratio: 0.5767
- Demographic parity difference: 0.2502
- Equal opportunity difference (salary): 0.0
- Equal opportunity difference (ranking): 0.069

## employment_type

| group | n | selection rate | top-10 rate | TPR salary | TPR ranking |
| --- | --- | --- | --- | --- | --- |
| contract | 48 | 0.3958 | 0.0 | 1.0 | 0.0 |
| full-time | 407 | 0.5111 | 0.0221 | 1.0 | 0.038 |
| part-time | 45 | 0.5556 | 0.0222 | 1.0 | 0.0333 |

- Disparate impact ratio: 0.7124
- Demographic parity difference: 0.1598
- Equal opportunity difference (salary): 0.0
- Equal opportunity difference (ranking): 0.038

## Flags

- city disparate impact ratio 0.5213 below 0.8
- city demographic parity difference 0.2938 over cap 0.2
- industry disparate impact ratio 0.5767 below 0.8
- industry demographic parity difference 0.2502 over cap 0.2
- employment_type disparate impact ratio 0.7124 below 0.8
