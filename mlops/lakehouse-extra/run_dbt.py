'''Materialize the gold marts defined in models/gold.

This is the local stand-in for dbt. No dbt is installed. The runner
reads each model file, expands {{ ref('name') }} to the table name,
and runs CREATE TABLE <mart> AS <query> against data/gold.db.
Staging tables come from notebooks/02_gold_marts.py, which must run
first. Each run drops and rebuilds the mart tables.
'''

import re
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'data' / 'gold.db'
MODELS_DIR = BASE / 'models' / 'gold'

REF_PATTERN = re.compile(r"\{\{\s*ref\('([^']+)'\)\s*\}\}")


def expand_refs(query):
    return REF_PATTERN.sub(r'\1', query)


def main():
    if not DB.exists():
        print('gold database not found, run notebooks/02_gold_marts.py first', file=sys.stderr)
        return 2
    conn = sqlite3.connect(DB)
    try:
        for model_file in sorted(MODELS_DIR.glob('*.sql')):
            name = model_file.stem
            query = expand_refs(model_file.read_text(encoding='utf-8'))
            conn.execute('DROP TABLE IF EXISTS %s' % name)
            conn.execute('CREATE TABLE %s AS %s' % (name, query))
            rows = conn.execute('SELECT COUNT(*) FROM %s' % name).fetchone()[0]
            print('%s rows=%d' % (name, rows))
        conn.commit()
    finally:
        conn.close()
    print('wrote %s' % DB.relative_to(BASE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
