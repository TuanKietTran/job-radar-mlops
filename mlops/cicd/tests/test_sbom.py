'''Tests for mlops/cicd/sbom.py.'''

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SBOM = ROOT / 'mlops' / 'cicd' / 'sbom.py'


class SbomTests(unittest.TestCase):
    def test_output_is_valid_spdx_with_sha256_per_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'one.py').write_text('value = 1\n', encoding='utf-8')
            (root / 'two.txt').write_text('hello\n', encoding='utf-8')
            output = root / 'sbom.spdx.json'
            result = subprocess.run(
                [sys.executable, str(SBOM), '--root', str(root), '--output', str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            document = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(document['spdxVersion'], 'SPDX-2.3')
            packages = document['packages']
            names = [package['name'] for package in packages]
            self.assertIn('python:3.15.0-slim-bookworm', names)
            self.assertIn('one.py', names)
            self.assertIn('two.txt', names)
            by_name = {package['name']: package for package in packages}
            expected = hashlib.sha256(b'value = 1\n').hexdigest()
            checksums = by_name['one.py']['checksums']
            self.assertEqual(len(checksums), 1)
            self.assertEqual(checksums[0]['algorithm'], 'SHA256')
            self.assertEqual(checksums[0]['checksumValue'], expected)
            self.assertEqual(len(document['documentDescribes']), len(packages))


if __name__ == '__main__':
    unittest.main()
