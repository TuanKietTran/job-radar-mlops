SELECT industry, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid
FROM {{ ref('staging_jobs') }}
GROUP BY industry
ORDER BY industry
