'''Tests for the metadata store and experiment tracking.'''

import tempfile
import unittest
from pathlib import Path

from mlops.metadata.store import MetadataStore, append_experiment, read_experiments
from mlops.registry.registry import main as registry_main
from mlops.training.train import main as train_main


class MetadataTest(unittest.TestCase):
    '''Metadata rows and experiment entries.'''

    def setUp(self):
        '''Create a temp metadata store.'''
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db_path = self.root / 'metadata.db'
        self.exp_path = self.root / 'experiments.jsonl'
        self.store = MetadataStore(self.db_path)
        self.addCleanup(self.store.close)

    def test_record_run_and_list(self):
        '''A training run is recorded and listed with decoded fields.'''
        run_id = self.store.record_run(model='salary', params={'seed': 42}, metrics={'mae': 1.5}, data_hash='abc')
        self.assertEqual(run_id, 1)
        runs = self.store.list_runs('salary')
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['params'], {'seed': 42})
        self.assertEqual(runs[0]['metrics'], {'mae': 1.5})
        self.assertEqual(runs[0]['data_hash'], 'abc')

    def test_record_model_stage_and_deployment(self):
        '''Model rows, stage updates and deployment rows.'''
        self.store.record_model(model='salary', version='v1', stage='dev', metrics={'mae': 1.5}, data_hash='abc', path='/tmp/v1')
        self.store.update_model_stage('salary', 'v1', 'production')
        record = self.store.get_model('salary', 'v1')
        self.assertEqual(record['stage'], 'production')
        self.store.record_deployment('salary', 'v1', 'production')
        self.assertEqual(len(self.store.list_deployments('salary')), 1)

    def test_experiments_jsonl(self):
        '''Experiment entries append and read back as JSON lines.'''
        append_experiment(self.exp_path, {'model': 'salary', 'metrics': {'mae': 1.5}})
        append_experiment(self.exp_path, {'model': 'ranking', 'metrics': {'precision_at_10': 0.8}})
        entries = read_experiments(self.exp_path)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['model'], 'salary')
        self.assertEqual(entries[1]['model'], 'ranking')

    def test_train_writes_run_and_experiment(self):
        '''A train call writes a run row and an experiment entry.'''
        out_dir = self.root / 'salary'
        result = train_main(['--model', 'salary', '--n', '120', '--seed', '42', '--out', str(out_dir), '--evaluate', '--metadata-db', str(self.db_path), '--experiments', str(self.exp_path)])
        self.assertEqual(result, 0)
        self.assertEqual(len(self.store.list_runs('salary')), 1)
        entries = read_experiments(self.exp_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['model'], 'salary')
        self.assertTrue(entries[0]['data_hash'])

    def test_register_writes_model_row(self):
        '''A register call writes a model row.'''
        out_dir = self.root / 'salary'
        train_main(['--model', 'salary', '--n', '120', '--seed', '42', '--out', str(out_dir), '--evaluate', '--metadata-db', str(self.db_path), '--experiments', str(self.exp_path)])
        models_root = self.root / 'models'
        result = registry_main(['register', '--model', 'salary', '--artifact', str(out_dir), '--metrics', str(out_dir / 'metrics.json'), '--root', str(models_root), '--metadata-db', str(self.db_path), '--experiments', str(self.exp_path)])
        self.assertEqual(result, 0)
        self.assertEqual(len(self.store.list_models('salary')), 1)


if __name__ == '__main__':
    unittest.main()
