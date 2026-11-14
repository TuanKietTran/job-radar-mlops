bash scripts/hygiene.sh
hygiene: pass
python3 mlops/cicd/check.py
check: pass
python3 docs/platform/check.py
check: PASS
python3 -m unittest discover mlops
............................................................................................./Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108e9be60>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108223060>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7a960>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7a420>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7a7a0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7ab20>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7ac00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7aea0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7adc0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7af80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b060>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b140>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b300>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b3e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b220>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b4c0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b5a0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b680>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b840>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b920>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7ba00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bca0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bae0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bd80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7be60>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c040>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c120>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c2e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c3c0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c200>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c4a0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c580>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c660>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c820>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c740>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900c9e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900d9a0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10900da80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
......../Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/synthetic.py:128: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bd80>
  overlap = len(set(candidate['skills']) & set(job['skills'])) / len(job['skills'])
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/synthetic.py:128: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bbc0>
  overlap = len(set(candidate['skills']) & set(job['skills'])) / len(job['skills'])
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.registry error: cannot move archived to staging
.registry error: cannot move dev to production
.registry error: no such registered version: salary v9
./Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bae0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7be60>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7bbc0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7ba00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b680>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b3e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b4c0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7b140>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7af80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x108f7aea0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.registry error: cannot move to production without a model card
.registry error: cannot move to staging without metrics
......
----------------------------------------------------------------------
Ran 113 tests in 5.549s

OK
bronze: 200 rows into 22 board files in bronze
silver: bronze 200 rows, dropped invalid 0, dedupe exact 0 fuzzy 0, kept 200 in jobs.db
gold: salary rows 36, board rows 22, month rows 11 in gold.db
validate: rows 200 valid 200 passed True report validation.json
  not_null_job_id: passed 200 failed 0
  not_null_title: passed 200 failed 0
  not_null_company: passed 200 failed 0
  not_null_city: passed 200 failed 0
  not_null_industry: passed 200 failed 0
  enum_city: passed 200 failed 0
  enum_industry: passed 200 failed 0
  enum_employment_type: passed 200 failed 0
  salary_ints: passed 200 failed 0
  salary_min_le_max: passed 200 failed 0
  salary_range: passed 200 failed 0
  experience_range: passed 200 failed 0
  posted_date_range: passed 200 failed 0
  job_id_unique: passed 1 failed 0
lineage: lineage.json sources 22 silver rows 200
bronze: 200 rows into 22 board files in bronze
silver: bronze 200 rows, dropped invalid 0, dedupe exact 0 fuzzy 0, kept 200 in jobs.db
gold: salary rows 36, board rows 22, month rows 11 in gold.db
validate: rows 200 valid 200 passed True report validation.json
  not_null_job_id: passed 200 failed 0
  not_null_title: passed 200 failed 0
  not_null_company: passed 200 failed 0
  not_null_city: passed 200 failed 0
  not_null_industry: passed 200 failed 0
  enum_city: passed 200 failed 0
  enum_industry: passed 200 failed 0
  enum_employment_type: passed 200 failed 0
  salary_ints: passed 200 failed 0
  salary_min_le_max: passed 200 failed 0
  salary_range: passed 200 failed 0
  experience_range: passed 200 failed 0
  posted_date_range: passed 200 failed 0
  job_id_unique: passed 1 failed 0
lineage: lineage.json sources 22 silver rows 200
bronze: 200 rows into 22 board files in bronze
silver: bronze 200 rows, dropped invalid 0, dedupe exact 0 fuzzy 0, kept 200 in jobs.db
gold: salary rows 36, board rows 22, month rows 11 in gold.db
validate: rows 200 valid 200 passed True report validation.json
  not_null_job_id: passed 200 failed 0
  not_null_title: passed 200 failed 0
  not_null_company: passed 200 failed 0
  not_null_city: passed 200 failed 0
  not_null_industry: passed 200 failed 0
  enum_city: passed 200 failed 0
  enum_industry: passed 200 failed 0
  enum_employment_type: passed 200 failed 0
  salary_ints: passed 200 failed 0
  salary_min_le_max: passed 200 failed 0
  salary_range: passed 200 failed 0
  experience_range: passed 200 failed 0
  posted_date_range: passed 200 failed 0
  job_id_unique: passed 1 failed 0
lineage: lineage.json sources 22 silver rows 200
bronze: 200 rows into 22 board files in bronze
silver: bronze 200 rows, dropped invalid 0, dedupe exact 0 fuzzy 0, kept 200 in jobs.db
gold: salary rows 36, board rows 22, month rows 11 in gold.db
validate: rows 200 valid 200 passed True report validation.json
  not_null_job_id: passed 200 failed 0
  not_null_title: passed 200 failed 0
  not_null_company: passed 200 failed 0
  not_null_city: passed 200 failed 0
  not_null_industry: passed 200 failed 0
  enum_city: passed 200 failed 0
  enum_industry: passed 200 failed 0
  enum_employment_type: passed 200 failed 0
  salary_ints: passed 200 failed 0
  salary_min_le_max: passed 200 failed 0
  salary_range: passed 200 failed 0
  experience_range: passed 200 failed 0
  posted_date_range: passed 200 failed 0
  job_id_unique: passed 1 failed 0
lineage: lineage.json sources 22 silver rows 200
bronze: 200 rows into 22 board files in bronze
silver: bronze 200 rows, dropped invalid 0, dedupe exact 0 fuzzy 0, kept 200 in jobs.db
gold: salary rows 36, board rows 22, month rows 11 in gold.db
validate: rows 200 valid 200 passed True report validation.json
  not_null_job_id: passed 200 failed 0
  not_null_title: passed 200 failed 0
  not_null_company: passed 200 failed 0
  not_null_city: passed 200 failed 0
  not_null_industry: passed 200 failed 0
  enum_city: passed 200 failed 0
  enum_industry: passed 200 failed 0
  enum_employment_type: passed 200 failed 0
  salary_ints: passed 200 failed 0
  salary_min_le_max: passed 200 failed 0
  salary_range: passed 200 failed 0
  experience_range: passed 200 failed 0
  posted_date_range: passed 200 failed 0
  job_id_unique: passed 1 failed 0
lineage: lineage.json sources 22 silver rows 200
validate: rows 200 valid 200 passed True report validation.json
  not_null_job_id: passed 200 failed 0
  not_null_title: passed 200 failed 0
  not_null_company: passed 200 failed 0
  not_null_city: passed 200 failed 0
  not_null_industry: passed 200 failed 0
  enum_city: passed 200 failed 0
  enum_industry: passed 200 failed 0
  enum_employment_type: passed 200 failed 0
  salary_ints: passed 200 failed 0
  salary_min_le_max: passed 200 failed 0
  salary_range: passed 200 failed 0
  experience_range: passed 200 failed 0
  posted_date_range: passed 200 failed 0
  job_id_unique: passed 1 failed 0
drift: alert field=salary psi=8.2831 ks=1.0
drift: ok salary psi=0.0 ks=0.0
report: wrote /var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpzb7mwd06/reports/report.md and /var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpzb7mwd06/reports/report.json
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpyv954qxc/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp17oaz_55/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmphwgs2k8r/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
evaluated salary: {"mae": 1480565.7434983717, "rmse": 1927272.7578420378, "rows": 120}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmptqxlibb1/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
trained ranking: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmptqxlibb1/ranking/model.json metrics={"mae": 0.025066695872721943, "precision_at_10": 0.34500000000000003, "queries": 20}
trained match: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmptqxlibb1/match/model.json metrics={"accuracy": 0.9625, "f1": 0.9662921348314606, "precision": 0.9347826086956522, "recall": 1.0, "rows": 80, "threshold": 0.3}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp9h439ilf/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
registered salary v2 at stage dev
promoted salary v1 to archived
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmparjiepbp/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpcorw6ajp/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
[
  {
    "metrics": {
      "mae": 2107084.5257877572,
      "rmse": 2717867.8312313054,
      "rows": 120,
      "test_rows": 24
    },
    "model": "salary",
    "stage": "dev",
    "version": "v1"
  }
]
{
  "kind": "linear_regression",
  "model": "salary",
  "path": "/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpcorw6ajp/models/salary/v1/model.json",
  "stage": "dev",
  "version": "v1"
}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp4r0txx8_/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
promoted salary v1 to staging
promoted salary v1 to production
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp9ape6sww/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
promoted salary v1 to staging
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpyr3w68m0/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp9g6bc9_2/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
.venv/bin/python -m pytest services/api/tests -q
...........................                                              [100%]
=============================== warnings summary ===============================
.venv/lib/python3.15/site-packages/fastapi/testclient.py:1
  /Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/.venv/lib/python3.15/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
27 passed, 1 warning in 0.37s
/Applications/Xcode.app/Contents/Developer/usr/bin/make smoke
.venv/bin/python -m services.salary.cli --gross 30000000 --dependents 1
{
  "gross": 30000000,
  "dependents": 1,
  "insurance": {
    "gross": 30000000,
    "bhxh_base": 30000000,
    "bhtn_base": 30000000,
    "bhxh_employee": 2400000,
    "bhyt_employee": 450000,
    "bhtn_employee": 300000,
    "employee_total": 3150000,
    "bhxh_employer": 5250000,
    "bhyt_employer": 900000,
    "bhtn_employer": 300000,
    "employer_total": 6450000
  },
  "taxable_income": 11450000,
  "tax": 967500,
  "net": 25882500
}
.venv/bin/python scripts/smoke.py
/Users/handlerone/Downloads/mlops-lab/wt/w-a-6-final/.venv/lib/python3.15/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
smoke: ok: jobs file holds at least one job
smoke: ok: ingest loads every job into SQLite
smoke: ok: ingest row count matches jobs file
smoke: ok: ingest round trip returns first job
smoke: ok: ingest round trip keeps skills as a list
smoke: ok: api health returns ok
smoke: ok: api jobs total matches jobs file
smoke: ok: api jobs returns at least one job
smoke: ok: api job detail returns first job
smoke: ok: api filters returns cities and levels
smoke: pass
git diff --check
