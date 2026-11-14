'''Run every warehouse query against data/gold.db.

Each file in sql/warehouse is executed in name order and its result
is written to results/<name>.csv. This is the local stand-in for a
Databricks SQL warehouse: the same SQL, run by the sqlite3 module.
'''

import csv
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'data' / 'gold.db'
SQL_DIR = BASE / 'sql' / 'warehouse'
OUTPUT_DIR = BASE / 'results'


def main():
    if not DB.exists():
        print('gold database not found, run notebooks/02_gold_marts.py first', file=sys.stderr)
        return 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    try:
        for sql_file in sorted(SQL_DIR.glob('*.sql')):
            query = sql_file.read_text(encoding='utf-8')
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            output = OUTPUT_DIR / (sql_file.stem + '.csv')
            with output.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerows(rows)
            print('%s rows=%d' % (sql_file.name, len(rows)))
    finally:
        conn.close()
    print('wrote %s' % OUTPUT_DIR.relative_to(BASE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
