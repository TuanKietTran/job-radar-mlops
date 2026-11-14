# Feature join evidence, MS-M1-6

Date: 2026-11-14
Branch: mlops/ms-m1-6-join
Base: 4f58a5c

## What was tested

A point-in-time join over a small table of training examples, each a
(job_id, as_of) pair, against the offline store built by
mlops/features/build.py. The join uses get_features(job_id, as_of),
which keeps the latest feature row with event_timestamp on or before
as_of and recomputes recency_days from as_of. No production code was
changed. No genuine bug was found in the run.

The build used the sample rows from test_features.py for job-early,
job-mid and job-late, plus two versioned rows for job-versioned
(posted 2026-01-10 with experience_years 2, and posted 2026-08-20
with experience_years 5). The build produced 5 jobs, 65 feature rows,
0 skipped rows.

The online store is latest-only and is not a point-in-time source.
It holds the latest values for each job, so it cannot answer what a
job looked like at an earlier as_of date. The join in
mlops/tests/test_features_join.py reads the offline store for the
point-in-time values and checks the online store only as a serving
lookup.

## Join table

| job_id | as_of | skill_count | experience_years | recency_days |
| --- | --- | --- | --- | --- |
| job-early | 2026-03-04 | 3 | 4 | 0 |
| job-early | 2026-05-01 | 3 | 4 | 58 |
| job-early | 2026-06-01 | 3 | 4 | 89 |
| job-early | 2026-11-14 | 3 | 4 | 255 |
| job-late | 2026-03-04 | empty | empty | empty |
| job-late | 2026-05-01 | empty | empty | empty |
| job-late | 2026-06-01 | empty | empty | empty |
| job-late | 2026-11-14 | 4 | 6 | 0 |
| job-versioned | 2026-03-04 | 3 | 2 | 53 |
| job-versioned | 2026-05-01 | 3 | 2 | 111 |
| job-versioned | 2026-06-01 | 3 | 2 | 142 |
| job-versioned | 2026-11-14 | 3 | 5 | 86 |

## Unknown job and expired entry

- Unknown job at 2026-11-14: offline get_features returns an empty
  result, online get returns an empty result.
- Online latest for job-versioned: experience_years 5, which matches
  the offline join at 2026-11-14 and differs from the offline join at
  2026-05-01, where experience_years is 2. The early join does not
  leak the latest online value.
- Expired online entry: a key set with ttl_seconds 0 returns an
  empty result from a whole-key serving lookup, and None for a
  single-feature serving lookup, while job-early still returns
  skill_count 3.

## Test results

- Feature tests: 18 tests, all passing, in 1.051s. That is 11 tests
  in test_features.py and 7 new tests in test_features_join.py.
- Full test suite: 101 tests, all passing, in 5.227s.

## Commands ran

From the worktree root:

- python3 -m unittest discover -s mlops/tests -p test_features*.py -v
- python3 -m unittest discover -s mlops/tests
- python3 /tmp/join_run.py

The join table above is the output of the join run script, which
built the stores from the same sample rows and versioned rows as the
new test file and printed one line per (job_id, as_of) pair.
