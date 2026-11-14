'''Tests for the stdlib runner: retries, dry-run, history, CLI.'''

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlops.orchestration import dagster_stub
from mlops.orchestration.dag import NODE_ORDER
from mlops.orchestration.run import backoff_for, describe_nodes, dry_run, main, make_subprocess_step, run_dag, run_with_retries


def stub_steps(calls, fail_nodes=None, flaky_nodes=None):
    fail_nodes = fail_nodes or set()
    flaky_nodes = flaky_nodes or {}
    steps = {}
    for name in NODE_ORDER:
        def make_step(node_name):
            def step():
                calls.append(node_name)
                if node_name in flaky_nodes:
                    flaky_nodes[node_name] -= 1
                    if flaky_nodes[node_name] >= 0:
                        raise RuntimeError('flaky ' + node_name)
                if node_name in fail_nodes:
                    raise RuntimeError('always fails ' + node_name)
            return step
        steps[name] = make_step(name)
    return steps


class TestRetries(unittest.TestCase):
    def test_backoff_sequence(self):
        self.assertEqual(backoff_for(0, [30, 60, 120]), 30)
        self.assertEqual(backoff_for(1, [30, 60, 120]), 60)
        self.assertEqual(backoff_for(2, [30, 60, 120]), 120)
        self.assertEqual(backoff_for(9, [30, 60, 120]), 120)

    def test_retries_then_succeeds(self):
        waits = []
        calls = {'n': 0}
        def step():
            calls['n'] += 1
            if calls['n'] < 3:
                raise RuntimeError('boom')
        ok, attempts, retries_used, error = run_with_retries(step, retries=3, sleep_fn=waits.append)
        self.assertTrue(ok)
        self.assertEqual(attempts, 3)
        self.assertEqual(retries_used, 2)
        self.assertIsNone(error)
        self.assertEqual(waits, [30, 60])

    def test_retries_then_fails_after_three(self):
        waits = []
        calls = {'n': 0}
        def step():
            calls['n'] += 1
            raise RuntimeError('boom')
        ok, attempts, retries_used, error = run_with_retries(step, retries=3, sleep_fn=waits.append)
        self.assertFalse(ok)
        self.assertEqual(attempts, 4)
        self.assertEqual(retries_used, 3)
        self.assertEqual(calls['n'], 4)
        self.assertEqual(waits, [30, 60, 120])
        self.assertIsNotNone(error)


class TestRunner(unittest.TestCase):
    def test_dry_run_lists_steps_without_executing(self):
        calls = []
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            lines = dry_run()
        text = buffer.getvalue()
        self.assertEqual(calls, [])
        self.assertEqual(len(lines), 6)
        for name in NODE_ORDER:
            self.assertIn(name, text)

    def test_runner_records_history(self):
        calls = []
        steps = stub_steps(calls, flaky_nodes={'train': 1})
        with tempfile.TemporaryDirectory() as tmp:
            run_id, records, all_ok = run_dag(steps=steps, runs_dir=tmp, run_id='test-run-1', sleep_fn=lambda s: None)
            self.assertTrue(all_ok)
            self.assertEqual(run_id, 'test-run-1')
            self.assertEqual([r['node'] for r in records], NODE_ORDER)
            self.assertEqual(calls.count('train'), 2)
            history = Path(tmp) / 'test-run-1.jsonl'
            self.assertTrue(history.is_file())
            rows = [json.loads(line) for line in history.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(rows), 6)
            for row in rows:
                self.assertEqual(row['run_id'], 'test-run-1')
                self.assertEqual(row['status'], 'success')
                self.assertIn('duration_seconds', row)
                self.assertIn('retries_used', row)
            train_row = [r for r in rows if r['node'] == 'train'][0]
            self.assertEqual(train_row['retries_used'], 1)

    def test_runner_stops_at_first_failure(self):
        calls = []
        steps = stub_steps(calls, fail_nodes={'train'})
        with tempfile.TemporaryDirectory() as tmp:
            run_id, records, all_ok = run_dag(steps=steps, runs_dir=tmp, run_id='test-run-2', sleep_fn=lambda s: None)
            self.assertFalse(all_ok)
            self.assertEqual([r['node'] for r in records], ['ingest', 'features', 'train'])
            self.assertEqual(records[-1]['status'], 'failed')
            self.assertEqual(records[-1]['retries_used'], 3)
            self.assertEqual(calls.count('train'), 4)
            self.assertNotIn('evaluate', calls)

    def test_only_runs_one_node(self):
        calls = []
        steps = stub_steps(calls)
        with tempfile.TemporaryDirectory() as tmp:
            run_id, records, all_ok = run_dag(steps=steps, only='train', runs_dir=tmp, run_id='test-run-3', sleep_fn=lambda s: None)
            self.assertTrue(all_ok)
            self.assertEqual([r['node'] for r in records], ['train'])
            self.assertEqual(calls, ['train'])

    def test_missing_step_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                run_dag(steps={}, runs_dir=tmp, run_id='test-run-4', sleep_fn=lambda s: None)

    def test_missing_entry_point_fails_loudly(self):
        node = {'name': 'ingest', 'entry_point': 'mlops/ingest/run.py', 'args': [], 'timeout_seconds': 60}
        step = make_subprocess_step(node, repo_root=Path(tempfile.mkdtemp()))
        with self.assertRaises(FileNotFoundError):
            step()

    def test_cli_list_and_dry_run(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(['--list'])
        self.assertEqual(code, 0)
        for name in NODE_ORDER:
            self.assertIn(name, buffer.getvalue())
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(['--dry-run'])
        self.assertEqual(code, 0)
        self.assertIn('ingest', buffer.getvalue())


class TestDagsterStub(unittest.TestCase):
    def test_stub_is_safe_without_dagster(self):
        self.assertFalse(dagster_stub.DAGSTER_AVAILABLE)
        self.assertEqual(dagster_stub.OPS, {})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = dagster_stub.main()
        self.assertEqual(code, 0)
        self.assertIn('Dagster is not installed', buffer.getvalue())


if __name__ == '__main__':
    unittest.main()
