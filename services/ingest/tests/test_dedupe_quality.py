'''Dedupe quality: labeled pairs from the dedupe-quality fixture.

The fixture holds labeled duplicate and non-duplicate job pairs.
This test runs is_duplicate over every pair with the fixture
threshold and permutation count and checks the confusion counts
and the precision, recall and F1 against the numbers recorded in
docs/evidence/mlops/dedupe-quality-report.md. If the report
numbers change, update the expected values here in the same
change so the test and the report stay in agreement.
'''

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ingest import dedupe as dedupe_mod

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'services' / 'ingest' / 'tests' / 'fixtures' / 'dedupe-quality.json'

EXPECTED_PAIRS = 49
EXPECTED_DUPLICATES = 25
EXPECTED_NON_DUPLICATES = 24
EXPECTED_TP = 19
EXPECTED_FP = 5
EXPECTED_FN = 6
EXPECTED_TN = 19
EXPECTED_PRECISION = 0.7917
EXPECTED_RECALL = 0.76
EXPECTED_F1 = 0.7755


def load_fixture():
    with FIXTURE.open(encoding='utf-8') as handle:
        return json.load(handle)


def compute_counts(fixture):
    perms = dedupe_mod._permutations(fixture['num_permutations'])
    threshold = fixture['threshold']
    tp = fp = fn = tn = 0
    for pair in fixture['pairs']:
        predicted, _, _, _ = dedupe_mod.is_duplicate(pair['job_a'], pair['job_b'], perms, threshold)
        expected = pair['expected_duplicate']
        if expected and predicted:
            tp += 1
        elif expected and not predicted:
            fn += 1
        elif not expected and predicted:
            fp += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def test_fixture_uses_default_threshold_and_permutations():
    fixture = load_fixture()
    assert fixture['threshold'] == dedupe_mod.THRESHOLD
    assert fixture['num_permutations'] == dedupe_mod.NUM_PERMUTATIONS
    assert len(fixture['pairs']) == EXPECTED_PAIRS
    duplicates = sum(1 for pair in fixture['pairs'] if pair['expected_duplicate'])
    assert duplicates == EXPECTED_DUPLICATES
    assert len(fixture['pairs']) - duplicates == EXPECTED_NON_DUPLICATES
    for pair in fixture['pairs']:
        assert pair['id']
        assert pair['category']
        assert pair['note']
        for key in ('title', 'company', 'city'):
            assert pair['job_a'][key]
            assert pair['job_b'][key]


def test_counts_and_metrics_match_report():
    fixture = load_fixture()
    tp, fp, fn, tn = compute_counts(fixture)
    assert (tp, fp, fn, tn) == (EXPECTED_TP, EXPECTED_FP, EXPECTED_FN, EXPECTED_TN)
    precision, recall, f1 = metrics(tp, fp, fn)
    assert precision == EXPECTED_PRECISION
    assert recall == EXPECTED_RECALL
    assert f1 == EXPECTED_F1
