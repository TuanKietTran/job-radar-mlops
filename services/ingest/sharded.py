'''Deterministic sharded ingest: split, per-shard dedupe, merged dedupe, sharded index.

The single-process path is services.ingest.normalize plus
services.ingest.dedupe over canonical jobs, with the search index
built by the vector_index formula: word tokens over title, company,
skills and description, document frequency, idf, L2-normalized
vectors rounded to five decimals.

This module keeps that behavior and runs it in parallel:

- split_jobs partitions canonical jobs by int(sha256(job id)) % N,
  the provisional split used until the coordinator publishes the
  final shard manifest. The split is deterministic and keeps
  input order inside each shard.
- Per-shard dedupe runs the same dedupe scan on each shard. A job
  that duplicates an earlier job inside the same shard is dropped
  there, exactly as the single-process scan would drop it.
- merge_kept re-scans the union of the per-shard kept jobs in
  global input order with the same duplicate predicate, so the
  merged kept set equals the single-process kept set. A cached
  comparison helper makes the merge fast: MinHash signatures and
  trigram sets are computed once per job, and the cheap exact
  Jaccard gates run before MinHash. The predicate is unchanged,
  only the evaluation order, so results are identical.
- build_sharded_index builds document frequencies per shard,
  sums them, then recomputes idf and normalized vectors from the
  merged frequencies. The merged index matches the single-process
  index.
- normalize_shards normalizes board fixture files in parallel
  and returns the same list as normalize_fixtures. Normalize over
  the current fixtures takes well under a second, so the parallel
  form exists for shape, not speed, and the benchmark reports
  honest numbers for it.

Shard files on disk are opt-in only: write_shards writes
shard-000.json and friends under the given directory. Nothing
here writes to the working tree unless asked.
'''

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

from services.ingest import dedupe as dedupe_mod
from services.ingest import normalize as normalize_mod


def shard_index(job_id, num_shards):
    digest = hashlib.sha256(str(job_id).encode('utf-8')).hexdigest()
    return int(digest, 16) % num_shards


def split_jobs(jobs, num_shards):
    if num_shards < 1:
        raise ValueError('num_shards must be at least 1')
    shards = [[] for _ in range(num_shards)]
    for job in jobs:
        shards[shard_index(job['id'], num_shards)].append(job)
    return shards


def canonical_text(job):
    text = ' '.join((job.get('title') or '', job.get('company') or '', job.get('city') or ''))
    return dedupe_mod._normalize_text(text)


def canonical_key(job):
    # Shared canonicalization: the key must stay identical to the
    # dedupe module, so it reuses its normalize helper.
    return hashlib.sha256(canonical_text(job).encode('utf-8')).hexdigest()


class _JobFacts:
    '''Precomputed per-job comparison data, built once per job.'''

    __slots__ = ('job', 'signature', 'title_company', 'full')

    def __init__(self, job, permutations):
        shingles = dedupe_mod.job_shingles(job)
        self.job = job
        self.signature = dedupe_mod.minhash_signature(shingles, permutations)
        self.title_company = dedupe_mod.title_company_shingles(job)
        self.full = shingles


def cached_pair_scores(left, right, threshold=dedupe_mod.THRESHOLD):
    '''The three dedupe scores, with the cheap exact gates first.

    dedupe.pair_scores computes MinHash first; this helper computes
    the two exact Jaccard scores first and skips MinHash when either
    is below threshold. The duplicate predicate is a conjunction,
    so skipping a pair that already fails a gate cannot change the
    outcome, and the returned scores are the same values.
    '''
    jac = dedupe_mod.jaccard(left.title_company, right.title_company)
    jac_full = dedupe_mod.jaccard(left.full, right.full)
    if jac < threshold or jac_full < threshold:
        return 0.0, jac, jac_full
    minhash = dedupe_mod.minhash_similarity(left.signature, right.signature)
    return minhash, jac, jac_full


def dedupe_with_cache(jobs, threshold=dedupe_mod.THRESHOLD, num_permutations=dedupe_mod.NUM_PERMUTATIONS):
    '''Same kept set and report shape as dedupe.dedupe_jobs.

    The scan order, the first-match rule and the report fields are
    copied from dedupe_jobs; only the comparison is cached, so the
    result must be identical. Tests prove it on the real data.
    '''
    permutations = dedupe_mod._permutations(num_permutations)
    facts = [_JobFacts(job, permutations) for job in jobs]
    kept = []
    kept_facts = []
    kept_ids = []
    duplicate_ids = []
    pairs = []
    for job, fact in zip(jobs, facts):
        match = None
        for kept_job, kept_fact in zip(kept, kept_facts):
            minhash, jac, jac_full = cached_pair_scores(fact, kept_fact, threshold)
            if minhash >= threshold and jac >= threshold and jac_full >= threshold:
                match = (kept_job, minhash, jac, jac_full)
                break
        if match is None:
            kept.append(job)
            kept_facts.append(fact)
            kept_ids.append(job['id'])
        else:
            kept_job, minhash, jac, jac_full = match
            duplicate_ids.append(job['id'])
            pairs.append({
                'kept': kept_job['id'],
                'duplicate': job['id'],
                'minhash_similarity': round(minhash, 4),
                'jaccard': round(jac, 4),
                'jaccard_title_company_city': round(jac_full, 4),
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


def _dedupe_shard(args):
    shard, threshold, num_permutations = args
    return dedupe_with_cache(shard, threshold, num_permutations)


def _worker_count(num_shards, workers):
    if workers is not None:
        return max(1, workers)
    return max(1, min(num_shards, os.cpu_count() or 1))


def run_shards(jobs, num_shards, workers=None, threshold=dedupe_mod.THRESHOLD, num_permutations=dedupe_mod.NUM_PERMUTATIONS):
    '''Split jobs and dedupe each shard, in parallel when asked.

    Returns (per_shard_kept, shard_sizes). Shard order is the split
    order, and input order is kept inside each shard.
    '''
    shards = split_jobs(jobs, num_shards)
    count = _worker_count(num_shards, workers)
    args = [(shard, threshold, num_permutations) for shard in shards]
    if count <= 1:
        results = [_dedupe_shard(item) for item in args]
    else:
        with Pool(processes=count) as pool:
            results = pool.map(_dedupe_shard, args)
    kept = [result[0] for result in results]
    sizes = [len(shard) for shard in shards]
    return kept, sizes


def merge_kept(per_shard_kept, jobs, threshold=dedupe_mod.THRESHOLD, num_permutations=dedupe_mod.NUM_PERMUTATIONS):
    '''Merge per-shard kept jobs into the single-process kept set.

    A job dropped inside its shard duplicates an earlier job of
    the same shard, which is earlier in global input order too, so
    the single-process scan would drop it as well. Re-scanning the
    union of the kept jobs in global input order with the same
    predicate therefore reproduces the single-process result.
    '''
    order = {job['id']: index for index, job in enumerate(jobs)}
    merged_input = [job for shard in per_shard_kept for job in shard]
    merged_input.sort(key=lambda job: order[job['id']])
    return dedupe_with_cache(merged_input, threshold, num_permutations)


def _word_tokens(text):
    '''Word tokens of a string: runs of alphanumeric characters plus underscore.

    This matches the word-character token rule used by the search
    index, including letter characters outside plain ASCII.
    '''
    tokens = []
    current = []
    for char in text.lower():
        if char == '_' or char.isalnum():
            current.append(char)
        elif current:
            tokens.append(''.join(current))
            current = []
    if current:
        tokens.append(''.join(current))
    return tokens


def doc_tokens(job):
    text = ' '.join([job.get('title') or '', job.get('company') or '', ' '.join(job.get('skills') or []), (job.get('description') or '')[:400]])
    return Counter(_word_tokens(text))


def _vectors(docs, idf):
    vecs = []
    for doc in docs:
        vec = {token: number * idf[token] for token, number in doc.items()}
        norm = math.sqrt(sum(value * value for value in vec.values())) or 1
        vecs.append({token: round(value / norm, 5) for token, value in vec.items()})
    return vecs


def build_index(jobs):
    '''Single-process search index, matching the vector_index formula.'''
    docs = [doc_tokens(job) for job in jobs]
    doc_freq = Counter()
    for doc in docs:
        doc_freq.update(doc.keys())
    count = len(jobs) or 1
    idf = {token: math.log((count + 1) / (freq + 1)) + 1 for token, freq in doc_freq.items()}
    return {'ids': [job['id'] for job in jobs], 'idf': idf, 'vecs': _vectors(docs, idf)}


def _shard_freq(shard):
    freq = Counter()
    for job in shard:
        freq.update(doc_tokens(job).keys())
    return freq


def build_sharded_index(jobs, num_shards, workers=None):
    '''Sharded search index: per-shard frequencies, merged idf.

    Document frequencies are summed across shards and idf is
    recomputed from the merged frequencies, so the merged index
    matches the single-process index.
    '''
    shards = split_jobs(jobs, num_shards)
    count = _worker_count(num_shards, workers)
    if count <= 1:
        freqs = [_shard_freq(shard) for shard in shards]
    else:
        with Pool(processes=count) as pool:
            freqs = pool.map(_shard_freq, shards)
    doc_freq = Counter()
    for freq in freqs:
        doc_freq.update(freq)
    total = len(jobs) or 1
    idf = {token: math.log((total + 1) / (freq + 1)) + 1 for token, freq in doc_freq.items()}
    docs = [doc_tokens(job) for job in jobs]
    return {'ids': [job['id'] for job in jobs], 'idf': idf, 'vecs': _vectors(docs, idf)}


def top_terms(vector, limit=5):
    return [token for token, _ in sorted(vector.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _normalize_file(path):
    return normalize_mod.normalize_board_file(path)


def normalize_shards(fixtures_dir, workers=None):
    '''Normalize board fixture files in parallel, same output as normalize_fixtures.'''
    root = Path(fixtures_dir)
    if not root.is_dir():
        raise ValueError('fixtures directory not found: ' + str(root))
    paths = sorted(root.glob('*.json'))
    count = _worker_count(len(paths) or 1, workers)
    if count <= 1 or len(paths) <= 1:
        return normalize_mod.normalize_fixtures(str(root))
    with Pool(processes=count) as pool:
        groups = pool.map(_normalize_file, paths)
    jobs = []
    for group in groups:
        jobs.extend(group)
    return jobs


def write_shards(jobs, num_shards, out_dir):
    '''Write shard files shard-000.json and friends under out_dir.'''
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    shards = split_jobs(jobs, num_shards)
    written = []
    for index, shard in enumerate(shards):
        path = out / ('shard-%03d.json' % index)
        with path.open('w', encoding='utf-8') as handle:
            json.dump(shard, handle, ensure_ascii=False, indent=2)
            print(file=handle)
        written.append(path)
    return written


def run_etl(fixtures_dir, num_shards, workers=None, threshold=dedupe_mod.THRESHOLD, num_permutations=dedupe_mod.NUM_PERMUTATIONS):
    '''Normalize, shard, dedupe per shard, merge, index. Returns a summary dict.'''
    started = time.perf_counter()
    jobs = normalize_shards(fixtures_dir, workers)
    normalize_seconds = time.perf_counter() - started
    started = time.perf_counter()
    per_shard_kept, shard_sizes = run_shards(jobs, num_shards, workers, threshold, num_permutations)
    kept, report = merge_kept(per_shard_kept, jobs, threshold, num_permutations)
    dedupe_seconds = time.perf_counter() - started
    started = time.perf_counter()
    index = build_sharded_index(kept, num_shards, workers)
    index_seconds = time.perf_counter() - started
    return {
        'jobs': len(jobs),
        'kept': len(kept),
        'duplicates': report['duplicates_count'],
        'shard_sizes': shard_sizes,
        'normalize_seconds': round(normalize_seconds, 3),
        'dedupe_seconds': round(dedupe_seconds, 3),
        'index_seconds': round(index_seconds, 3),
        'report': report,
        'index': index,
    }


def benchmark(jobs, shard_counts=(2, 4, 8), workers=None):
    '''Time single-process vs sharded paths on the given jobs.'''
    rows = []
    started = time.perf_counter()
    kept, _ = dedupe_mod.dedupe_jobs(jobs)
    build_index(kept)
    single_seconds = time.perf_counter() - started
    rows.append({'shards': 1, 'seconds': round(single_seconds, 3), 'rows_per_second': round(len(jobs) / single_seconds, 1) if single_seconds else 0.0})
    for num_shards in shard_counts:
        started = time.perf_counter()
        per_shard_kept, _ = run_shards(jobs, num_shards, workers)
        merged, _ = merge_kept(per_shard_kept, jobs)
        build_sharded_index(merged, num_shards, workers)
        seconds = time.perf_counter() - started
        rows.append({'shards': num_shards, 'seconds': round(seconds, 3), 'rows_per_second': round(len(jobs) / seconds, 1) if seconds else 0.0})
    return rows


def load_jobs(path):
    return dedupe_mod.load_jobs(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Sharded ingest: split, per-shard dedupe, merge, index, benchmark.')
    parser.add_argument('--jobs', default='data/processed/jobs.json', help='input path for canonical jobs')
    parser.add_argument('--fixtures', default='data/fixtures/boards', help='directory holding board fixture files')
    parser.add_argument('--from-fixtures', action='store_true', help='run the full ETL from fixture files instead of canonical jobs')
    parser.add_argument('--shards', type=int, default=4, help='number of shards')
    parser.add_argument('--workers', type=int, default=None, help='parallel workers (default: CPU count, capped by shards)')
    parser.add_argument('--write-shards', default=None, help='directory to write shard files under')
    parser.add_argument('--out', default=None, help='output path for merged kept jobs')
    parser.add_argument('--benchmark', action='store_true', help='time single-process vs sharded paths and print the table')
    args = parser.parse_args(argv)
    if args.from_fixtures:
        summary = run_etl(args.fixtures, args.shards, args.workers)
        print('sharded etl ' + str(summary['jobs']) + ' jobs ' + str(summary['kept']) + ' kept ' + str(summary['duplicates']) + ' duplicates ' + str(summary['normalize_seconds']) + 's normalize ' + str(summary['dedupe_seconds']) + 's dedupe ' + str(summary['index_seconds']) + 's index')
        return 0
    jobs = load_jobs(args.jobs)
    if args.benchmark:
        for row in benchmark(jobs, workers=args.workers):
            print('shards=' + str(row['shards']) + ' seconds=' + str(row['seconds']) + ' rows_per_second=' + str(row['rows_per_second']))
        return 0
    per_shard_kept, sizes = run_shards(jobs, args.shards, args.workers)
    kept, report = merge_kept(per_shard_kept, jobs)
    index = build_sharded_index(kept, args.shards, args.workers)
    if args.write_shards:
        write_shards(jobs, args.shards, args.write_shards)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('w', encoding='utf-8') as handle:
            json.dump(kept, handle, ensure_ascii=False, indent=2)
            print(file=handle)
    print('sharded ' + str(len(kept)) + ' kept ' + str(report['duplicates_count']) + ' duplicates ' + str(args.shards) + ' shards sizes=' + str(sizes) + ' docs=' + str(len(index['ids'])) + ' vocab=' + str(len(index['idf'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
