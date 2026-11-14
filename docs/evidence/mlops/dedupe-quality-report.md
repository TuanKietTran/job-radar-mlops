# Dedupe quality report

## Scope

- Branch: plat/ms-p1-2-dedupe
- Base commit: 0b43897
- Fixture and test commit: c0385e973d205f85764c157df26cdf9f5d7b7873
- Report commit: the commit directly after the fixture and test commit on the same branch
- Code measured: services/ingest/dedupe.py as of the base commit, unchanged by this work

## Method

Each labeled pair was run once through is_duplicate with the default threshold 0.85 and 128 permutations (seed 42). A pair counts as duplicate only when all three gates pass: MinHash similarity at or above 0.85, exact Jaccard similarity over title and company trigrams at or above 0.85, and exact Jaccard similarity over title, company and city trigrams at or above 0.85. Trigrams are character trigrams over normalized text (lowercase, full stops replaced by spaces, whitespace collapsed). Counts follow the usual definitions: TP is a labeled duplicate predicted duplicate, FP is a labeled non-duplicate predicted duplicate, FN is a labeled duplicate predicted non-duplicate, TN is a labeled non-duplicate predicted non-duplicate. Precision is TP divided by TP plus FP. Recall is TP divided by TP plus FN. F1 is the harmonic mean of precision and recall. All three are rounded to 4 decimals. No threshold tuning was done.

## Fixture

- File: services/ingest/tests/fixtures/dedupe-quality.json
- Pairs: 49 (25 expected duplicates, 24 expected non-duplicates)
- Each pair holds an id, a category, job a, job b, expected duplicate true or false, and a short note
- Jobs use the canonical schema from the ingest brief: id, title, company, city, industry, skills, salary range in VND, remote, experience range, level, employment type, posted date, source board, source URL under example.invalid, description, benefits, application deadline
- All companies, titles and boards are invented, and all text is synthetic
- Fixture text is unaccented, so diacritic variants are not covered by this measurement

## Results

|  | Predicted duplicate | Predicted non-duplicate |
| --- | --- | --- |
| Expected duplicate | TP 19 | FN 6 |
| Expected non-duplicate | FP 5 | TN 19 |

- Precision: 19 / (19 + 5) = 0.7917
- Recall: 19 / (19 + 6) = 0.76
- F1: 0.7755

## Per-category breakdown

| Category | Pairs | TP | FP | FN | TN |
| --- | --- | --- | --- | --- | --- |
| identical | 3 | 3 | 0 | 0 | 0 |
| case | 3 | 3 | 0 | 0 | 0 |
| punctuation | 3 | 3 | 0 | 0 | 0 |
| whitespace | 3 | 3 | 0 | 0 | 0 |
| near-title | 3 | 2 | 0 | 1 | 0 |
| near-company | 3 | 1 | 0 | 2 | 0 |
| near-city | 2 | 1 | 0 | 1 | 0 |
| combined | 2 | 2 | 0 | 0 | 0 |
| borderline-duplicate | 3 | 1 | 0 | 2 | 0 |
| same-role-diff-city | 5 | 0 | 0 | 0 | 5 |
| same-role-diff-company | 5 | 0 | 0 | 0 | 5 |
| diff-role-same-company-city | 5 | 0 | 0 | 0 | 5 |
| diff-role-diff-company-city | 2 | 0 | 0 | 0 | 2 |
| diff-role-diff-company-diff-city | 2 | 0 | 0 | 0 | 2 |
| borderline-non-duplicate | 5 | 0 | 5 | 0 | 0 |

## Failure analysis

Scores below are MinHash, Jaccard over title and company, and Jaccard over title, company and city, in that order.

### False positives (5)

All five are borderline non-duplicates where the two jobs differ by one word in one short field while title and company (or title and city) are identical, so the trigram sets still overlap enough to clear all three gates.

- non-20: Ky su phan mem Python at Cong ty TNHH An Binh, Hai Phong vs Hai Duong. Scores 0.8984, 1.0, 0.88. City differs by one word only.
- non-21: Lap trinh vien Frontend at Cong ty TNHH Minh Khang, Binh Duong vs Binh Dinh. Scores 0.9141, 1.0, 0.9038. City differs by one word only.
- non-22: Chuyen vien phan tich du lieu at Cong ty Co phan Sao Mai, Dong Nai vs Dong Thap. Scores 0.8672, 1.0, 0.8909. City differs by one word only.
- non-23: Ky su phan mem Python at Cong ty TNHH An Binh vs Cong ty TNHH An Binh Tech, Ho Chi Minh. Scores 0.9453, 0.8864, 0.9091. Company gains one word only.
- non-24: Lap trinh vien Frontend at Cong ty Co phan Sao Mai vs Cong ty Co phan Sao Mai Group, Da Nang. Scores 0.875, 0.88, 0.8644. Company gains one word only.

The city gate separates postings when city strings differ by more than a word (Ho Chi Minh vs Ha Noi reads 0.72 on the title, company and city Jaccard), but two city names that share a first word and differ only in the second pass the gate, as do company names that differ by a single trailing word.

### False negatives (6)

In all six, the exact Jaccard gates are the binding constraint: adding or dropping words in a short title or company changes a large share of trigrams, so exact similarity falls below 0.85 even when MinHash stays near or above it.

- dup-15: Chuyen vien kiem thu phan mem vs Chuyen vien kiem thu, Cong ty TNHH Binh Minh, Da Nang. Scores 0.8672, 0.7917, 0.8182. Title loses two words.
- dup-16: Ky su phan mem Python, Cong ty TNHH An Binh vs Cong ty An Binh, Ho Chi Minh. Scores 0.8594, 0.825, 0.8627. Company loses its legal form.
- dup-18: Lap trinh vien Frontend, Tap doan Cong nghe Binh Minh vs Cong ty Cong nghe Binh Minh, Da Nang. Scores 0.8047, 0.7255, 0.7586. Company legal form differs.
- dup-20: Chuyen vien phan tich du lieu, Cong ty Co phan Sao Mai, Ha Noi vs Thanh pho Ha Noi. Scores 0.8438, 1.0, 0.8361. City gains a prefix.
- dup-24: Ky su phan mem Python vs Ky su phan mem Python Django, Cong ty Co phan Sao Mai, Ha Noi. Scores 0.875, 0.8043, 0.8302. Title gains one framework word.
- dup-25: Chuyen vien phan tich du lieu vs Chuyen vien du lieu, Cong ty TNHH Binh Minh, Da Nang. Scores 0.8281, 0.7551, 0.8. Title loses two words.

### Near-threshold correct rejections

Two same-role, different-city pairs were rejected by a single gate, which shows the three-gate conjunction doing its job: non-03 (Ha Noi vs Hai Phong) reads 0.8203 on MinHash and 0.8571 on the title, company and city Jaccard, so MinHash alone rejects it; non-05 (Binh Duong vs Dong Nai) reads 0.875 on MinHash and 0.8393 on the title, company and city Jaccard, so that Jaccard alone rejects it.

## Test

- File: services/ingest/tests/test_dedupe_quality.py
- The test loads the fixture, recomputes the counts with the same is_duplicate call, and asserts the counts and the precision, recall and F1 shown above
- Command, run from the worktree root: uvx --with pytest pytest services/ingest/tests -q
- System python has no pytest installed, so uvx supplied it
- Result: 21 passed in 49.97s

## Notes and limits

- The fixture holds 49 hand-built pairs, not a sample of production boards, so the precision and recall describe this fixture only
- The borderline pairs were chosen as pairs whose lowest gate score falls near 0.85, which is why most of the errors sit in the borderline categories
- No change was made to services/ingest/dedupe.py: the false positives and false negatives follow from the trigram method and the 0.85 threshold, not from a defect in the implementation against its documented design
