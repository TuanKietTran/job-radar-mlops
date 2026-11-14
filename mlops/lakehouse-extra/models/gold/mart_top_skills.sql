SELECT skill, COUNT(*) AS postings
FROM {{ ref('job_skills') }}
GROUP BY skill
ORDER BY postings DESC, skill
