SELECT city, industry, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid,
  MIN(salary_gross_min) AS min_salary,
  MAX(salary_gross_max) AS max_salary
FROM staging_jobs
GROUP BY city, industry
ORDER BY city, industry;
