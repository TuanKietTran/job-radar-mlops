python3 -m venv .venv
.venv/bin/pip install --upgrade pip
Requirement already satisfied: pip in ./.venv/lib/python3.15/site-packages (26.2.1)
Collecting pip
  Using cached pip-26.3-py3-none-any.whl.metadata (4.6 kB)
Using cached pip-26.3-py3-none-any.whl (2.0 MB)
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 26.2.1
    Uninstalling pip-26.2.1:
      Successfully uninstalled pip-26.2.1
Successfully installed pip-26.3
.venv/bin/pip install -r services/api/requirements.txt -r services/ai/requirements.txt
Collecting fastapi (from -r services/api/requirements.txt (line 1))
  Using cached fastapi-0.163.0-py3-none-any.whl.metadata (27 kB)
Collecting uvicorn (from -r services/api/requirements.txt (line 2))
  Using cached uvicorn-0.54.0-py3-none-any.whl.metadata (6.6 kB)
Collecting pytest (from -r services/api/requirements.txt (line 3))
  Using cached pytest-9.2.0-py3-none-any.whl.metadata (7.9 kB)
Collecting httpx (from -r services/api/requirements.txt (line 4))
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting starlette>=0.46.0 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached starlette-1.10.0-py3-none-any.whl.metadata (6.6 kB)
Collecting anyio>=4.1.0 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached anyio-4.16.0-py3-none-any.whl.metadata (4.7 kB)
Collecting pydantic>=2.9.0 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached pydantic-2.14.3-py3-none-any.whl.metadata (141 kB)
Collecting typing-extensions>=4.8.0 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
Collecting typing-inspection>=0.4.2 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached typing_inspection-0.4.5-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached annotated_doc-0.0.6-py3-none-any.whl.metadata (6.5 kB)
Collecting opentelemetry-api>=1.44.0 (from fastapi->-r services/api/requirements.txt (line 1))
  Using cached opentelemetry_api-1.45.2-py3-none-any.whl.metadata (1.4 kB)
Collecting click>=7.0 (from uvicorn->-r services/api/requirements.txt (line 2))
  Using cached click-8.5.1-py3-none-any.whl.metadata (2.6 kB)
Collecting h11>=0.8 (from uvicorn->-r services/api/requirements.txt (line 2))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting iniconfig>=2 (from pytest->-r services/api/requirements.txt (line 3))
  Using cached iniconfig-2.3.1-py3-none-any.whl.metadata (2.8 kB)
Collecting packaging>=24 (from pytest->-r services/api/requirements.txt (line 3))
  Using cached packaging-26.3-py3-none-any.whl.metadata (3.5 kB)
Collecting pluggy<2,>=1.6 (from pytest->-r services/api/requirements.txt (line 3))
  Using cached pluggy-1.7.0-py3-none-any.whl.metadata (5.0 kB)
Collecting pygments>=2.15 (from pytest->-r services/api/requirements.txt (line 3))
  Using cached pygments-2.21.0-py3-none-any.whl.metadata (2.5 kB)
Collecting certifi (from httpx->-r services/api/requirements.txt (line 4))
  Using cached certifi-2026.10.23-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx->-r services/api/requirements.txt (line 4))
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx->-r services/api/requirements.txt (line 4))
  Using cached idna-3.20-py3-none-any.whl.metadata (7.2 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.9.0->fastapi->-r services/api/requirements.txt (line 1))
  Using cached annotated_types-0.8.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.50.4 (from pydantic>=2.9.0->fastapi->-r services/api/requirements.txt (line 1))
  Using cached pydantic_core-2.50.4-cp315-cp315-macosx_11_0_arm64.whl.metadata (6.6 kB)
Using cached fastapi-0.163.0-py3-none-any.whl (154 kB)
Using cached uvicorn-0.54.0-py3-none-any.whl (87 kB)
Using cached pytest-9.2.0-py3-none-any.whl (411 kB)
Using cached pluggy-1.7.0-py3-none-any.whl (27 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached annotated_doc-0.0.6-py3-none-any.whl (5.3 kB)
Using cached anyio-4.16.0-py3-none-any.whl (134 kB)
Using cached click-8.5.1-py3-none-any.whl (126 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached idna-3.20-py3-none-any.whl (69 kB)
Using cached iniconfig-2.3.1-py3-none-any.whl (7.6 kB)
Using cached opentelemetry_api-1.45.2-py3-none-any.whl (60 kB)
Using cached packaging-26.3-py3-none-any.whl (129 kB)
Using cached pydantic-2.14.3-py3-none-any.whl (494 kB)
Using cached pydantic_core-2.50.4-cp315-cp315-macosx_11_0_arm64.whl (2.1 MB)
Using cached annotated_types-0.8.0-py3-none-any.whl (13 kB)
Using cached pygments-2.21.0-py3-none-any.whl (1.3 MB)
Using cached starlette-1.10.0-py3-none-any.whl (80 kB)
Using cached typing_extensions-4.16.0-py3-none-any.whl (45 kB)
Using cached typing_inspection-0.4.5-py3-none-any.whl (14 kB)
Using cached certifi-2026.10.23-py3-none-any.whl (135 kB)
Installing collected packages: typing-extensions, pygments, pluggy, packaging, iniconfig, idna, h11, click, certifi, annotated-types, annotated-doc, uvicorn, typing-inspection, pytest, pydantic-core, opentelemetry-api, httpcore, anyio, starlette, pydantic, httpx, fastapi

Successfully installed annotated-doc-0.0.6 annotated-types-0.8.0 anyio-4.16.0 certifi-2026.10.23 click-8.5.1 fastapi-0.163.0 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.2 packaging-26.3 pluggy-1.7.0 pydantic-2.14.3 pydantic-core-2.50.4 pygments-2.21.0 pytest-9.2.0 starlette-1.10.0 typing-extensions-4.16.0 typing-inspection-0.4.5 uvicorn-0.54.0
bash scripts/hygiene.sh
hygiene: pass
python3 mlops/cicd/check.py
check: pass
python3 docs/platform/check.py
check: PASS
python3 -m unittest discover mlops
............................................................................................./private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x1084f7300>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109163bc0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925ab20>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925adc0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925ac00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925af80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925ace0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b300>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b220>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b3e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b4c0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b5a0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b760>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b680>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b840>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b920>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925ba00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bbc0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bca0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bd80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925be60>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294200>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294040>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x1092942e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x1092943c0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x1092944a0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294660>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294740>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294820>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294580>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294900>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x1092949e0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294ba0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294c80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294ac0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109294d60>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109295e00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x109295ee0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
......../private/tmp/fresh-a6/mlops/training/synthetic.py:128: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925be60>
  overlap = len(set(candidate['skills']) & set(job['skills'])) / len(job['skills'])
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/synthetic.py:128: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bca0>
  overlap = len(set(candidate['skills']) & set(job['skills'])) / len(job['skills'])
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.registry error: cannot move archived to staging
.registry error: cannot move dev to production
.registry error: no such registered version: salary v9
./private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bd80>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bae0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925bca0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b920>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b760>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b220>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b4c0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925b140>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925ace0>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/private/tmp/fresh-a6/mlops/training/linear.py:46: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10925ac00>
  standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.registry error: cannot move to production without a model card
.registry error: cannot move to staging without metrics
......
----------------------------------------------------------------------
Ran 113 tests in 5.846s

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
report: wrote /var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpg6pj22_f/reports/report.md and /var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpg6pj22_f/reports/report.json
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpjb6toq93/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpnp40b2y3/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp8jbl7yfy/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
evaluated salary: {"mae": 1480565.7434983717, "rmse": 1927272.7578420378, "rows": 120}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpyr8q2ojx/salary/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
trained ranking: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpyr8q2ojx/ranking/model.json metrics={"mae": 0.025066695872721943, "precision_at_10": 0.34500000000000003, "queries": 20}
trained match: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpyr8q2ojx/match/model.json metrics={"accuracy": 0.9625, "f1": 0.9662921348314606, "precision": 0.9347826086956522, "recall": 1.0, "rows": 80, "threshold": 0.3}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpfgt540mm/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
registered salary v2 at stage dev
promoted salary v1 to archived
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp4jzu3p3g/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp03j7uflo/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
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
  "path": "/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp03j7uflo/models/salary/v1/model.json",
  "stage": "dev",
  "version": "v1"
}
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpwdedxuz_/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
promoted salary v1 to staging
promoted salary v1 to production
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmpeaso4g5a/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
promoted salary v1 to staging
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmphfsb8v2a/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
trained salary: model=/var/folders/9l/02yf95314nq1n2gtb78g5nbh0000gn/T/tmp3tybqgqu/artifact/model.json metrics={"mae": 2107084.5257877572, "rmse": 2717867.8312313054, "rows": 120, "test_rows": 24}
registered salary v1 at stage dev
.venv/bin/python -m pytest services/api/tests -q
...........................                                              [100%]
=============================== warnings summary ===============================
.venv/lib/python3.15/site-packages/fastapi/testclient.py:1
  /private/tmp/fresh-a6/.venv/lib/python3.15/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
27 passed, 1 warning in 0.49s
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
/private/tmp/fresh-a6/.venv/lib/python3.15/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
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
