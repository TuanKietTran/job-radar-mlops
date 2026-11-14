'''Deduplicate canonical jobs across boards.

A pair is a duplicate when all three gates pass at threshold 0.85:

- MinHash similarity over character trigrams of the normalized
  title, company and city, using seeded permutations over
  SHA-256 shingle hashes, so the estimate is deterministic.
- Exact Jaccard similarity over character trigrams of the
  normalized title and company.
- Exact Jaccard similarity over the same title, company and city
  trigrams the MinHash estimates. The estimate alone is not
  enough: it read 0.8828 for one distinct pair whose exact
  similarity is 0.8421, so the exact check decides.

Title and company alone would merge distinct postings for the
same role at the same company in different cities. The city
checks stop those pairs from merging.

Keep first: jobs are scanned in input order and a job that
duplicates any already kept job is recorded as a duplicate of
that kept job. Same input gives same output.
'''

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

THRESHOLD = 0.85
NUM_PERMUTATIONS = 128
SEED = 42
PRIME = 2305843009213693951


def _normalize_text(value):
    return ' '.join(str(value).strip().lower().replace('.', ' ').split())


def trigrams(text):
    normalized = _normalize_text(text)
    if len(normalized) < 3:
        return {normalized}
    return {normalized[i:i + 3] for i in range(len(normalized) - 2)}


def job_shingles(job):
    text = ' '.join((job.get('title') or '', job.get('company') or '', job.get('city') or ''))
    return trigrams(text)


def title_company_shingles(job):
    text = ' '.join((job.get('title') or '', job.get('company') or ''))
    return trigrams(text)


def jaccard(left, right):
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


def _base_hash(shingle):
    digest = hashlib.sha256(shingle.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], 'big')


def _permutations(count=NUM_PERMUTATIONS, seed=SEED):
    rng = random.Random(seed)
    return [(rng.randrange(1, PRIME), rng.randrange(0, PRIME)) for _ in range(count)]


def minhash_signature(shingles, permutations):
    if not shingles:
        return tuple(0 for _ in permutations)
    bases = [_base_hash(shingle) for shingle in shingles]
    return tuple(min((a * base + b) % PRIME for base in bases) for a, b in permutations)


def minhash_similarity(left, right):
    if not left or not right:
        return 0.0
    matches = sum(1 for a, b in zip(left, right) if a == b)
    return matches / len(left)


def pair_scores(job_a, job_b, permutations):
    minhash = minhash_similarity(
        minhash_signature(job_shingles(job_a), permutations),
        minhash_signature(job_shingles(job_b), permutations),
    )
    jac = jaccard(title_company_shingles(job_a), title_company_shingles(job_b))
    jac_tcc = jaccard(job_shingles(job_a), job_shingles(job_b))
    return minhash, jac, jac_tcc


def is_duplicate(job_a, job_b, permutations, threshold=THRESHOLD):
    minhash, jac, jac_tcc = pair_scores(job_a, job_b, permutations)
    duplicate = minhash >= threshold and jac >= threshold and jac_tcc >= threshold
    return duplicate, minhash, jac, jac_tcc


def dedupe_jobs(jobs, threshold=THRESHOLD, num_permutations=NUM_PERMUTATIONS):
    permutations = _permutations(num_permutations)
    kept = []
    kept_ids = []
    duplicate_ids = []
    pairs = []
    for job in jobs:
        match = None
        for kept_job in kept:
            duplicate, minhash, jac, jac_tcc = is_duplicate(job, kept_job, permutations, threshold)
            if duplicate:
                match = (kept_job, minhash, jac, jac_tcc)
                break
        if match is None:
            kept.append(job)
            kept_ids.append(job['id'])
        else:
            kept_job, minhash, jac, jac_tcc = match
            duplicate_ids.append(job['id'])
            pairs.append({
                'kept': kept_job['id'],
                'duplicate': job['id'],
                'minhash_similarity': round(minhash, 4),
                'jaccard': round(jac, 4),
                'jaccard_title_company_city': round(jac_tcc, 4),
            })
    report = {
        'total': len(jobs),
        'kept_count': len(kept_ids),
        'duplicates_count': len(duplicate_ids),
        'kept': kept_ids,
        'duplicates': duplicate_ids,
        'pairs': pairs,
        'threshold': threshold,
        'num_permutations': num_permutations,
    }
    return kept, report


def load_jobs(path):
    with Path(path).open(encoding='utf-8') as handle:
        jobs = json.load(handle)
    if not isinstance(jobs, list):
        raise ValueError('jobs file must hold a list: ' + str(path))
    return jobs


def main(argv=None):
    parser = argparse.ArgumentParser(description='Deduplicate canonical jobs and write a dedupe report.')
    parser.add_argument('--in', '--jobs', dest='input', default='data/processed/jobs.json', help='input path for canonical jobs')
    parser.add_argument('--out', default='data/processed/dedupe-report.json', help='output path for the dedupe report')
    parser.add_argument('--threshold', type=float, default=THRESHOLD, help='similarity threshold for both gates')
    parser.add_argument('--permutations', type=int, default=NUM_PERMUTATIONS, help='number of MinHash permutations')
    args = parser.parse_args(argv)
    jobs = load_jobs(args.input)
    _, report = dedupe_jobs(jobs, threshold=args.threshold, num_permutations=args.permutations)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print('deduplicated ' + str(report['total']) + ' jobs to ' + str(report['kept_count']) + ' kept, ' + str(report['duplicates_count']) + ' duplicates to ' + str(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
