SELECT skill, COUNT(*) AS postings
FROM job_skills
GROUP BY skill
ORDER BY postings DESC, skill;
