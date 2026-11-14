SELECT CASE WHEN experience_years BETWEEN 0 AND 2 THEN 'junior' WHEN experience_years BETWEEN 3 AND 5 THEN 'mid' WHEN experience_years BETWEEN 6 AND 9 THEN 'senior' WHEN experience_years BETWEEN 10 AND 15 THEN 'lead' END AS band, COUNT(*) AS postings,
  CAST(AVG((salary_gross_min + salary_gross_max) / 2.0) AS INTEGER) AS avg_salary_mid,
  MIN(salary_gross_min) AS min_salary,
  MAX(salary_gross_max) AS max_salary
FROM staging_jobs
GROUP BY band
ORDER BY band;
