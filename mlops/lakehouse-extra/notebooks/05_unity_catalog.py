# %md
# # Unity Catalog mapping
#
# Databricks equivalent: a Unity Catalog metastore holding
# catalog.schema.table entries with owners and grants. Here the catalog
# is the file catalog.yml at the lakehouse root, and the metastore
# outputs are data/catalog/mapping.csv and data/catalog/lineage.csv.
# Every entry must resolve to a real file or SQLite table and must
# have an owner and at least one grant. Run with plain python3.
#
# %md
# ## Read and validate the catalog
#
# catalog.yml uses a small plain subset of YAML: one entry per table,
# fields as key value pairs, grants as a list of role and permissions.
# No YAML library is used, the lines are read directly.

import csv
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CATALOG = BASE / 'catalog.yml'
DB = BASE / 'data' / 'gold.db'
MAPPING = BASE / 'data' / 'catalog' / 'mapping.csv'
LINEAGE = BASE / 'data' / 'catalog' / 'lineage.csv'

DERIVED_FROM = {
    ('bronze', 'jobs'): '',
    ('silver', 'jobs'): 'bronze.jobs',
    ('silver', 'silver_jobs'): 'silver.jobs',
    ('gold', 'staging_jobs'): 'silver.jobs',
}


def parse_catalog(text):
    catalog = None
    tables = []
    entry = None
    grant = None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith('#'):
            continue
        if raw == 'tables:':
            continue
        if raw.startswith('catalog: '):
            catalog = raw.split(':', 1)[1].strip()
            continue
        if raw.startswith('  - catalog: '):
            entry = {'grants': []}
            tables.append(entry)
            grant = None
            entry['catalog'] = raw.split(':', 1)[1].strip()
            continue
        if raw.startswith('      - role: '):
            grant = {'role': raw.split(':', 1)[1].strip()}
            entry['grants'].append(grant)
            continue
        if raw.startswith('        permissions: '):
            grant['permissions'] = [
                item.strip()
                for item in raw.split(':', 1)[1].split(',')
            ]
            continue
        if raw.startswith('    ') and raw.strip().endswith(':'):
            continue
        if raw.startswith('    ') and ': ' in raw:
            key, value = raw.strip().split(':', 1)
            entry[key.strip()] = value.strip()
            continue
        raise ValueError('cannot parse line: ' + raw)
    return catalog, tables


def local_target_exists(entry):
    target = entry['local_target']
    if target.endswith('.db'):
        if not DB.exists():
            return False
        conn = sqlite3.connect(DB)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type='table' AND name=?",
                (entry['table'],)).fetchone()
            return row[0] == 1
        finally:
            conn.close()
    return (BASE / target).exists()


def derived_from(entry):
    key = (entry['schema'], entry['table'])
    if key in DERIVED_FROM:
        return DERIVED_FROM[key]
    if entry['schema'] == 'gold':
        return 'gold.staging_jobs'
    return ''


def main():
    if not CATALOG.exists():
        print('catalog file not found: catalog.yml', file=sys.stderr)
        return 2
    catalog, tables = parse_catalog(CATALOG.read_text(encoding='utf-8'))
    if catalog != 'main':
        print('catalog must be main', file=sys.stderr)
        return 2
    errors = []
    for entry in tables:
        name = '%s.%s.%s' % (
            entry.get('catalog'), entry.get('schema'), entry.get('table'))
        if entry.get('catalog') != 'main':
            errors.append(name + ' is not in catalog main')
        if not entry.get('owner'):
            errors.append(name + ' has no owner')
        if not entry.get('grants'):
            errors.append(name + ' has no grants')
        if not local_target_exists(entry):
            errors.append(name + ' local target missing: ' + entry.get('local_target', ''))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    MAPPING.parent.mkdir(parents=True, exist_ok=True)
    with MAPPING.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['catalog', 'schema', 'table', 'local_target', 'owner'])
        for entry in tables:
            writer.writerow([
                entry['catalog'], entry['schema'], entry['table'],
                entry['local_target'], entry['owner']])
    with LINEAGE.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['source', 'table', 'derived_from'])
        for entry in tables:
            name = '%s.%s' % (entry['schema'], entry['table'])
            writer.writerow([entry['local_target'], name, derived_from(entry)])
    for entry in tables:
        print('%s.%s.%s -> %s (%s)' % (
            entry['catalog'], entry['schema'], entry['table'],
            entry['local_target'], entry['owner']))
    print('wrote %s' % MAPPING.relative_to(BASE))
    print('wrote %s' % LINEAGE.relative_to(BASE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
