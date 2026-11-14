# Lakehouse extras

A Databricks-style lakehouse layer that runs locally on SQLite and CSV
files, with synthetic data only. It stands in for Delta Lake, Unity
Catalog, Databricks SQL and dbt so the full flow can be checked on a
fresh clone with plain python3 and the standard library.

## Mapping

| Databricks concept | Local equivalent |
| --- | --- |
| Delta table | Versioned CSV snapshots under data/delta/silver_jobs/, one file per version |
| Delta log | data/delta/silver_jobs/_delta_log/ with one JSON entry per version, fields version, operation, rows, source |
| Unity Catalog catalog.schema.table | SQLite table named schema_table, for example gold mart tables named mart_salary_by_city_industry |
| Unity Catalog catalog | catalog.yml listing main.bronze, main.silver and main.gold tables with owner and grants, checked by notebooks/05_unity_catalog.py |
| Databricks SQL warehouse | run_sql.py and notebooks/03_warehouse_queries.py running sql/warehouse/*.sql against data/gold.db |
| Notebook job | A runnable python3 script in notebooks/, with %md-style comment cells |
| dbt model | A SQL file in models/gold/ using ref(), materialized by run_dbt.py |

## Layout

- fixture.py writes 200 synthetic postings to data/jobs.csv
- notebooks/01_bronze_to_silver.py cleans bronze into data/silver/jobs.csv
- notebooks/02_gold_marts.py builds staging tables and eight gold marts in data/gold.db
- notebooks/03_warehouse_queries.py runs the warehouse queries into data/warehouse/
- notebooks/04_delta_lake.py builds versioned Delta snapshots v0001 and v0002 under data/delta/silver_jobs/ with one log entry per version
- notebooks/05_unity_catalog.py validates catalog.yml and writes data/catalog/mapping.csv and data/catalog/lineage.csv
- catalog.yml lists 12 tables in catalog main across schemas bronze, silver and gold, each with owner data-team and grants
- sql/warehouse/ holds the eight warehouse queries
- run_sql.py runs those queries into results/
- models/gold/ holds the eight dbt-style marts, models/schema.yml describes them
- mart_salary_by_experience_band: band, postings, avg_salary_mid, min_salary, max_salary
- mart_postings_by_source_board: source_board, postings, share
- mart_postings_by_industry: industry, postings, avg_salary_mid
- mart_salary_by_month: month, postings, avg_salary_mid, min_salary, max_salary
- run_dbt.py expands ref() and materializes each mart as a SQLite table
- tests/ holds stdlib unittest checks for the fixture, notebooks, SQL, dbt runner, Delta versions and Unity Catalog mapping

## Run

From the repo root, in order:

```
python3 mlops/lakehouse-extra/fixture.py
python3 mlops/lakehouse-extra/notebooks/01_bronze_to_silver.py
python3 mlops/lakehouse-extra/notebooks/02_gold_marts.py
python3 mlops/lakehouse-extra/notebooks/03_warehouse_queries.py
python3 mlops/lakehouse-extra/notebooks/04_delta_lake.py
python3 mlops/lakehouse-extra/notebooks/05_unity_catalog.py
python3 mlops/lakehouse-extra/run_sql.py
python3 mlops/lakehouse-extra/run_dbt.py
```

Then the tests:

```
python3 -m unittest discover -s mlops/lakehouse-extra/tests -v
```

## Data

Seed 42 is the default everywhere, so two runs of the fixture produce
the same file. Columns are job_id, title, company, city, industry,
remote, experience_years, salary_gross_min, salary_gross_max, currency,
employment_type, posted_date, source_board and skills. Currency is
always VND. Remote is onsite, hybrid or remote. Salaries are gross
monthly VND. Skills are semicolon-joined in the CSV and split into
the job_skills staging table by notebook 02.

Generated files under data/ and results/ are not committed. They are
rebuilt by the commands above. The evidence log for a full run is at
docs/evidence/mlops/lakehouse-extra-run.log.

## dbt note

dbt is not installed and is not required. run_dbt.py is the local
stand-in: it reads each model, replaces ref('name') with the table
name, and runs CREATE TABLE <mart> AS <query>. The mart SQL matches
the warehouse SQL row for row, and the tests check that the SQL
results and the mart tables hold the same row counts.
