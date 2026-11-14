'''Tests for DAG definition, validation, schedules and sensors.'''

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlops.orchestration.dag import NODE_ORDER, NODES, get_node, get_nodes, get_schedules, get_sensors, new_data_available, drift_alert_triggered, sensor_should_trigger, topological_order, validate_dag


class TestDagOrder(unittest.TestCase):
    def test_order_is_fixed(self):
        self.assertEqual(NODE_ORDER, ['ingest', 'features', 'train', 'evaluate', 'register', 'deploy'])
        self.assertEqual(validate_dag(), NODE_ORDER)
        self.assertEqual(topological_order(), NODE_ORDER)

    def test_nodes_have_dependencies_in_order(self):
        for name in NODE_ORDER:
            node = get_node(name)
            for dep in node['depends_on']:
                self.assertLess(NODE_ORDER.index(dep), NODE_ORDER.index(name))

    def test_every_node_has_retries_timeouts_entry(self):
        for node in get_nodes():
            self.assertEqual(node['retries'], 3)
            self.assertEqual(node['backoff_seconds'], [30, 60, 120])
            self.assertGreater(node['timeout_seconds'], 0)
            self.assertTrue(node['entry_point'].startswith('mlops/'))

    def test_entry_points_match_brief(self):
        self.assertEqual(NODES['ingest']['entry_point'], 'mlops/ingest/run.py')
        self.assertEqual(NODES['features']['entry_point'], 'mlops/features/build.py')
        self.assertEqual(NODES['train']['entry_point'], 'mlops/training/train.py')
        self.assertEqual(NODES['evaluate']['entry_point'], 'mlops/training/train.py')
        self.assertEqual(NODES['evaluate']['args'], ['--evaluate'])
        self.assertEqual(NODES['register']['entry_point'], 'mlops/registry/registry.py')
        self.assertEqual(NODES['deploy']['entry_point'], 'mlops/serving/app.py')
        self.assertEqual(NODES['deploy']['args'], ['--check'])

    def test_cycle_is_rejected(self):
        cyclic = {
            'a': {'depends_on': ['b'], 'retries': 3, 'timeout_seconds': 60, 'entry_point': 'mlops/x.py'},
            'b': {'depends_on': ['a'], 'retries': 3, 'timeout_seconds': 60, 'entry_point': 'mlops/y.py'},
        }
        with self.assertRaises(ValueError):
            topological_order(cyclic)

    def test_unknown_dependency_is_rejected(self):
        bad = {
            'a': {'depends_on': ['missing'], 'retries': 3, 'timeout_seconds': 60, 'entry_point': 'mlops/x.py'},
        }
        with self.assertRaises(ValueError):
            topological_order(bad)

    def test_unknown_node_raises(self):
        with self.assertRaises(ValueError):
            get_node('nope')


class TestSchedulesAndSensors(unittest.TestCase):
    def test_schedules(self):
        schedules = {item['name']: item for item in get_schedules()}
        self.assertEqual(schedules['daily_ingest']['cron'], '0 2 * * *')
        self.assertEqual(schedules['daily_ingest']['nodes'], ['ingest'])
        self.assertEqual(schedules['weekly_retrain']['cron'], '0 2 * * 0')
        self.assertEqual(schedules['weekly_retrain']['nodes'], NODE_ORDER)
        for item in get_schedules():
            self.assertEqual(item['timezone'], 'Asia/Ho_Chi_Minh')

    def test_sensor_names(self):
        names = [item['name'] for item in get_sensors()]
        self.assertIn('new_bronze_data', names)
        self.assertIn('drift_alert', names)

    def test_new_data_available(self):
        self.assertEqual(new_data_available(['a.parquet'], ['a.parquet', 'b.parquet']), ['b.parquet'])
        self.assertEqual(new_data_available(['a.parquet'], ['a.parquet']), [])
        self.assertEqual(new_data_available([], ['a.parquet']), ['a.parquet'])

    def test_drift_thresholds_are_strictly_over(self):
        self.assertTrue(drift_alert_triggered(0.21, 0.0))
        self.assertTrue(drift_alert_triggered(0.0, 0.16))
        self.assertFalse(drift_alert_triggered(0.2, 0.15))
        self.assertFalse(drift_alert_triggered(0.0, 0.0))

    def test_sensor_should_trigger(self):
        self.assertTrue(sensor_should_trigger('new_bronze_data', {'known_files': ['a'], 'current_files': ['a', 'b']}))
        self.assertFalse(sensor_should_trigger('new_bronze_data', {'known_files': ['a'], 'current_files': ['a']}))
        self.assertTrue(sensor_should_trigger('drift_alert', {'psi': 0.3, 'ks': 0.0}))
        self.assertFalse(sensor_should_trigger('drift_alert', {'psi': 0.1, 'ks': 0.1}))
        with self.assertRaises(ValueError):
            sensor_should_trigger('nope', {})


if __name__ == '__main__':
    unittest.main()
