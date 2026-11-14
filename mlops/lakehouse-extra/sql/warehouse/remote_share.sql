SELECT remote, COUNT(*) AS postings,
  CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM staging_jobs) AS share
FROM staging_jobs
GROUP BY remote
ORDER BY remote;
