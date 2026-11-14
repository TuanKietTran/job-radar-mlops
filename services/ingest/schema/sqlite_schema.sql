-- SQLite schema for the ingest store.
-- Jobs hold canonical normalized jobs. Raw payloads hold the
-- verbatim board payload for each board-local job id.

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  city TEXT NOT NULL,
  industry TEXT NOT NULL,
  skills TEXT NOT NULL DEFAULT '[]',
  salary_min_vnd INTEGER,
  salary_max_vnd INTEGER,
  salary_currency TEXT NOT NULL DEFAULT 'VND',
  remote TEXT NOT NULL,
  experience_min_years INTEGER NOT NULL,
  experience_max_years INTEGER NOT NULL,
  level TEXT NOT NULL,
  employment_type TEXT NOT NULL,
  posted_at TEXT NOT NULL,
  source_board TEXT NOT NULL,
  source_url TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  benefits TEXT NOT NULL DEFAULT '[]',
  application_deadline TEXT,
  CHECK (remote IN ('onsite', 'hybrid', 'remote')),
  CHECK (level IN ('intern', 'junior', 'middle', 'senior', 'lead')),
  CHECK (employment_type IN ('full-time', 'part-time', 'contract', 'internship')),
  CHECK (salary_currency = 'VND'),
  CHECK (salary_min_vnd IS NULL OR salary_min_vnd >= 0),
  CHECK (salary_max_vnd IS NULL OR salary_max_vnd >= 0),
  CHECK (salary_min_vnd IS NULL OR salary_max_vnd IS NULL OR salary_min_vnd <= salary_max_vnd),
  CHECK (experience_min_years >= 0),
  CHECK (experience_max_years >= experience_min_years)
);

CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs (city);
CREATE INDEX IF NOT EXISTS idx_jobs_industry ON jobs (industry);
CREATE INDEX IF NOT EXISTS idx_jobs_source_board ON jobs (source_board);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs (posted_at);

CREATE TABLE IF NOT EXISTS raw_payloads (
  board TEXT NOT NULL,
  board_job_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  PRIMARY KEY (board, board_job_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_payloads_board ON raw_payloads (board);
