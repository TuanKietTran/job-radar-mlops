'''Metadata store: SQLite records for datasets, runs, models and deployments, plus experiment tracking in JSONL.

Every train and register call writes a row here. Experiment entries
record params, metrics, data hash and the git commit when available.
'''

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMA = '''
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    data_hash TEXT,
    rows INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    model TEXT NOT NULL,
    params TEXT NOT NULL,
    metrics TEXT NOT NULL,
    data_hash TEXT,
    git_commit TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY,
    model TEXT NOT NULL,
    version TEXT NOT NULL,
    stage TEXT NOT NULL,
    metrics TEXT NOT NULL,
    data_hash TEXT,
    path TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(model, version)
);
CREATE TABLE IF NOT EXISTS deployments (
    id INTEGER PRIMARY KEY,
    model TEXT NOT NULL,
    version TEXT NOT NULL,
    stage TEXT NOT NULL,
    created_at TEXT NOT NULL
);
'''


def _decode(row):
    '''Convert a SQLite row to a dict with JSON fields decoded.'''
    item = dict(row)
    for key in ('params', 'metrics'):
        if key in item and item[key] is not None:
            item[key] = json.loads(item[key])
    return item


class MetadataStore:
    '''SQLite metadata store for datasets, runs, models, deployments.'''

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def _now(self):
        '''Return the current UTC timestamp.'''
        return datetime.now(timezone.utc).isoformat()

    def record_dataset(self, name, data_hash, rows):
        '''Record a dataset and return its row id.'''
        cursor = self.connection.execute('INSERT INTO datasets (name, data_hash, rows, created_at) VALUES (?, ?, ?, ?)', (name, data_hash, rows, self._now()))
        self.connection.commit()
        return cursor.lastrowid

    def record_run(self, model, params, metrics, data_hash, git_commit=None):
        '''Record a training run and return its row id.'''
        cursor = self.connection.execute('INSERT INTO runs (model, params, metrics, data_hash, git_commit, created_at) VALUES (?, ?, ?, ?, ?, ?)', (model, json.dumps(params, sort_keys=True), json.dumps(metrics, sort_keys=True), data_hash, git_commit, self._now()))
        self.connection.commit()
        return cursor.lastrowid

    def record_model(self, model, version, stage, metrics, data_hash, path):
        '''Record a registered model version and return its row id.'''
        cursor = self.connection.execute('INSERT OR REPLACE INTO models (model, version, stage, metrics, data_hash, path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (model, version, stage, json.dumps(metrics, sort_keys=True), data_hash, path, self._now()))
        self.connection.commit()
        return cursor.lastrowid

    def update_model_stage(self, model, version, stage):
        '''Update the stage of a registered model version.'''
        cursor = self.connection.execute('UPDATE models SET stage = ? WHERE model = ? AND version = ?', (stage, model, version))
        self.connection.commit()
        return cursor.rowcount

    def record_deployment(self, model, version, stage):
        '''Record a deployment and return its row id.'''
        cursor = self.connection.execute('INSERT INTO deployments (model, version, stage, created_at) VALUES (?, ?, ?, ?)', (model, version, stage, self._now()))
        self.connection.commit()
        return cursor.lastrowid

    def list_runs(self, model=None):
        '''Return training runs, newest last, optionally for one model.'''
        if model:
            rows = self.connection.execute('SELECT * FROM runs WHERE model = ? ORDER BY id', (model,)).fetchall()
        else:
            rows = self.connection.execute('SELECT * FROM runs ORDER BY id').fetchall()
        return [_decode(row) for row in rows]

    def list_models(self, model=None):
        '''Return registered models, optionally for one model.'''
        if model:
            rows = self.connection.execute('SELECT * FROM models WHERE model = ? ORDER BY id', (model,)).fetchall()
        else:
            rows = self.connection.execute('SELECT * FROM models ORDER BY id').fetchall()
        return [_decode(row) for row in rows]

    def get_model(self, model, version):
        '''Return one registered model version, or None.'''
        row = self.connection.execute('SELECT * FROM models WHERE model = ? AND version = ?', (model, version)).fetchone()
        return _decode(row) if row else None

    def list_deployments(self, model=None):
        '''Return deployments, optionally for one model.'''
        if model:
            rows = self.connection.execute('SELECT * FROM deployments WHERE model = ? ORDER BY id', (model,)).fetchall()
        else:
            rows = self.connection.execute('SELECT * FROM deployments ORDER BY id').fetchall()
        return [dict(row) for row in rows]

    def close(self):
        '''Close the database connection.'''
        self.connection.close()


def append_experiment(path, entry):
    '''Append one experiment entry as a JSON line.'''
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps(entry, sort_keys=True, default=str) + '\n')


def read_experiments(path):
    '''Read experiment entries from a JSONL file.'''
    entries = []
    path = Path(path)
    if not path.is_file():
        return entries
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def main(argv=None):
    '''List metadata records from the command line.'''
    parser = argparse.ArgumentParser(description='List metadata records.')
    parser.add_argument('command', choices=['list-runs', 'list-models', 'list-deployments'], help='what to list')
    parser.add_argument('--model', default=None, help='only list this model')
    parser.add_argument('--db', default=None, help='metadata database path')
    args = parser.parse_args(argv)
    db_path = Path(args.db) if args.db else PROJECT_ROOT / 'mlops' / 'metadata' / 'metadata.db'
    store = MetadataStore(db_path)
    if args.command == 'list-runs':
        records = store.list_runs(args.model)
    elif args.command == 'list-models':
        records = store.list_models(args.model)
    else:
        records = store.list_deployments(args.model)
    print(json.dumps(records, indent=2, sort_keys=True, default=str))
    store.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
