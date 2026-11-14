SELECT remote, COUNT(*) AS postings,
  CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM {{ ref('staging_jobs') }}) AS share
FROM {{ ref('staging_jobs') }}
GROUP BY remote
ORDER BY remote
