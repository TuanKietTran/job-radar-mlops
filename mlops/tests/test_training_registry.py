'''Tests for the model registry and its stage guards.'''

import json
import tempfile
import unittest
from pathlib import Path

from mlops.metadata.store import MetadataStore
from mlops.registry.registry import main as registry_main
from mlops.training.train import main as train_main


class RegistryTest(unittest.TestCase):
    '''Register, promote, list and load tests.'''

    def setUp(self):
        '''Train one model artifact in a temp directory.'''
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.artifact = self.root / 'artifact'
        self.db_path = self.root / 'metadata.db'
        self.exp_path = self.root / 'experiments.jsonl'
        self.models_root = self.root / 'models'
        result = train_main(['--model', 'salary', '--n', '120', '--seed', '42', '--out', str(self.artifact), '--evaluate', '--metadata-db', str(self.db_path), '--experiments', str(self.exp_path)])
        self.assertEqual(result, 0)

    def _register(self, with_metrics=True):
        args = ['register', '--model', 'salary', '--artifact', str(self.artifact), '--root', str(self.models_root), '--metadata-db', str(self.db_path), '--experiments', str(self.exp_path)]
        if with_metrics:
            args += ['--metrics', str(self.artifact / 'metrics.json')]
        return registry_main(args)

    def _version_dir(self, version='v1'):
        return self.models_root / 'salary' / version

    def test_register_creates_layout(self):
        '''Register writes model, metadata, card and stage files.'''
        self.assertEqual(self._register(), 0)
        version_dir = self._version_dir()
        self.assertTrue((version_dir / 'model.json').is_file())
        self.assertTrue((version_dir / 'metadata.json').is_file())
        self.assertTrue((version_dir / 'card.md').is_file())
        self.assertEqual((version_dir / 'stage.txt').read_text(encoding='utf-8').strip(), 'dev')
        with open(version_dir / 'metadata.json', encoding='utf-8') as handle:
            metadata = json.load(handle)
        self.assertEqual(metadata['stage'], 'dev')
        self.assertTrue(metadata['evaluation'])
        self.assertTrue(metadata['metrics'])
        store = MetadataStore(self.db_path)
        record = store.get_model('salary', 'v1')
        self.assertIsNotNone(record)
        self.assertEqual(record['stage'], 'dev')
        store.close()

    def test_promote_flow(self):
        '''Dev to staging to production works with metrics and a card.'''
        self.assertEqual(self._register(), 0)
        self.assertEqual(registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'staging', '--root', str(self.models_root), '--metadata-db', str(self.db_path)]), 0)
        self.assertEqual(registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'production', '--root', str(self.models_root), '--metadata-db', str(self.db_path)]), 0)
        self.assertEqual((self._version_dir() / 'stage.txt').read_text(encoding='utf-8').strip(), 'production')
        store = MetadataStore(self.db_path)
        self.assertEqual(len(store.list_deployments('salary')), 1)
        store.close()

    def test_promote_to_staging_requires_metrics(self):
        '''Staging is refused without metrics.'''
        self.assertEqual(self._register(with_metrics=False), 0)
        result = registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'staging', '--root', str(self.models_root), '--metadata-db', str(self.db_path)])
        self.assertEqual(result, 2)
        self.assertEqual((self._version_dir() / 'stage.txt').read_text(encoding='utf-8').strip(), 'dev')

    def test_promote_to_production_requires_card_and_evaluation(self):
        '''Production is refused without a card and an evaluation run.'''
        self.assertEqual(self._register(), 0)
        self.assertEqual(registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'staging', '--root', str(self.models_root), '--metadata-db', str(self.db_path)]), 0)
        version_dir = self._version_dir()
        (version_dir / 'card.md').unlink()
        metadata_path = version_dir / 'metadata.json'
        with open(metadata_path, encoding='utf-8') as handle:
            metadata = json.load(handle)
        metadata['evaluation'] = False
        with open(metadata_path, 'w', encoding='utf-8') as handle:
            json.dump(metadata, handle, indent=2, sort_keys=True)
        result = registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'production', '--root', str(self.models_root), '--metadata-db', str(self.db_path)])
        self.assertEqual(result, 2)

    def test_invalid_transition_refused(self):
        '''Dev cannot jump straight to production.'''
        self.assertEqual(self._register(), 0)
        result = registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'production', '--root', str(self.models_root), '--metadata-db', str(self.db_path)])
        self.assertEqual(result, 2)

    def test_archive_and_second_version(self):
        '''Any stage can be archived, and versions increment.'''
        self.assertEqual(self._register(), 0)
        self.assertEqual(self._register(), 0)
        self.assertTrue(self._version_dir('v2').is_dir())
        self.assertEqual(registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'archived', '--root', str(self.models_root), '--metadata-db', str(self.db_path)]), 0)
        self.assertEqual(registry_main(['promote', '--model', 'salary', '--version', 'v1', '--to', 'staging', '--root', str(self.models_root), '--metadata-db', str(self.db_path)]), 2)

    def test_list_and_load(self):
        '''List and load work, and unknown versions fail.'''
        self.assertEqual(self._register(), 0)
        self.assertEqual(registry_main(['list', '--root', str(self.models_root)]), 0)
        self.assertEqual(registry_main(['load', '--model', 'salary', '--version', 'v1', '--root', str(self.models_root)]), 0)
        self.assertEqual(registry_main(['load', '--model', 'salary', '--version', 'v9', '--root', str(self.models_root)]), 2)


if __name__ == '__main__':
    unittest.main()
