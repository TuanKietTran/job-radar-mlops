SELECT source_board, COUNT(*) AS postings,
  CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM {{ ref('staging_jobs') }}) AS share
FROM {{ ref('staging_jobs') }}
GROUP BY source_board
ORDER BY source_board
