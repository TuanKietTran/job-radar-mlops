# %md
# # Warehouse queries
#
# Databricks equivalent: a Databricks SQL warehouse running the queries
# in sql/warehouse. Here the warehouse is the SQLite database at
# data/gold.db, read with the standard sqlite3 module. Each query result
# is written to data/warehouse as a CSV. Run with plain python3.
#
# %md
# ## Run every warehouse query
#
# Query files are read in name order. A missing gold database means
# notebook 02 has not run yet, so the script stops with that message
# instead of reporting empty results.

import csv
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DB = BASE / 'data' / 'gold.db'
SQL_DIR = BASE / 'sql' / 'warehouse'
OUTPUT_DIR = BASE / 'data' / 'warehouse'


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
