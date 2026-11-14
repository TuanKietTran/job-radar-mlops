SELECT source_board, COUNT(*) AS postings,
  CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM staging_jobs) AS share
FROM staging_jobs
GROUP BY source_board
ORDER BY source_board;
