# Feature store

Features for the salary, ranking and match models, built from silver
data into an offline store for training and an online store for
serving. Standard library only, deterministic seed 42 wherever a
choice needs one.

## Feature list

| Feature | Group | Type | Meaning |
| --- | --- | --- | --- |
| experience_years | salary | int | Years of experience required by the job, 0 to 15 |
| city | salary | string | City of the job posting |
| industry | salary | string | Industry of the hiring company |
| skill_count | salary | int | Number of skills listed on the job |
| seniority_band | salary | string | junior 0 to 2, mid 3 to 5, senior 6 to 9, lead 10 to 15 |
| remote_flag | salary | bool | Whether the job allows remote work |
| skill_overlap | ranking | float | Share of the reference profile skills that the job lists |
| salary_fit | ranking | float | Fit of the reference expected salary inside the posted band |
| recency_days | ranking | int | Days between the posting date and the reference date |
| remote_match | ranking | float | 1 when the job is remote and the profile expects remote work |
| text_overlap | match | float | Jaccard overlap of job title plus industry tokens with profile text |
| skill_coverage | match | float | Share of the job listed skills covered by the profile |
| experience_gap | match | int | Profile experience minus the experience the job requires |

Every feature is defined with name, type, owner and description in
mlops/features/registry.py. The registry is the source of truth; the
stores and the Feast mapping follow it.

Ranking and match features compare each job with one fixed reference
profile, defined in registry.py: skills python, sql, aws, docker;
experience 5 years; expects remote work; expected salary 30,000,000
VND gross. One profile for every row keeps values reproducible from
the silver row alone.

## Build the stores

Run from the repo root.

    python3 -m mlops.features.build --help
    python3 -m mlops.features.build
    python3 -m mlops.features.build --silver mlops/data/lake/silver/jobs.db --offline mlops/features/offline.db --online mlops/features/online.db

The builder reads silver as jobs.db, jobs.csv or jobs.jsonl. When no
silver store exists yet, it builds from the shipped fixture
mlops/features/fixtures/silver_sample.csv and says so in its output.

## Query point-in-time features

    from mlops.features.build import get_features
    features = get_features('job-0005', '2026-06-01', 'mlops/features/offline.db')

Only rows with an event timestamp on or before as_of are returned,
so a read at 2026-06-01 sees nothing for a job posted 2026-11-14.
recency_days is recomputed from as_of, so the same row answers at
any date.

## Online store

    from mlops.features.online import OnlineStore
    store = OnlineStore('mlops/features/online.db', log_path='online_latency.log')
    store.get('job-0005')

TTL is 3600 seconds per key by default, set with --ttl at build
time. Every lookup writes one latency log line with key, hit and
latency in milliseconds. The Redis mapping is in feast_mapping.md.

## Determinism

Rebuilding from the same silver data gives the same offline feature
rows. Online expiry times depend on the build clock and are excluded
from that guarantee.

## Tests

    python3 -m unittest discover -s mlops/tests -p test_features*.py
