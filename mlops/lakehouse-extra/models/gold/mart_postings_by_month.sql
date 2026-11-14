SELECT substr(posted_date, 1, 7) AS month, COUNT(*) AS postings
FROM {{ ref('staging_jobs') }}
GROUP BY month
ORDER BY month
