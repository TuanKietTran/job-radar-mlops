'''Tests for mlops/cicd/sbom.py.'''

import hashlib
import importlib.util
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

    def test_image_packages_listed_without_docker(self):
        spec = importlib.util.spec_from_file_location('sbom', SBOM)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        text = json.dumps([{'name': 'fastapi', 'version': '0.115'}, {'name': 'bad'}])
        self.assertEqual(module._pip_packages(text), [('fastapi', '0.115')])
        self.assertEqual(module._pip_packages('not json'), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'one.py').write_text('value = 1\n', encoding='utf-8')
            document, count = module.build_sbom(root, 'python:3.15.0-slim-bookworm', image='job-radar-api:local', image_packages=[('fastapi', '0.115')], image_id='sha256:abc')
            self.assertEqual(count, 1)
            by_id = {package['SPDXID']: package for package in document['packages']}
            self.assertEqual(by_id['SPDXRef-Package-built-image']['name'], 'job-radar-api:local')
            self.assertEqual(by_id['SPDXRef-Package-built-image']['versionInfo'], 'sha256:abc')
            self.assertEqual(by_id['SPDXRef-ImagePackage-fastapi']['versionInfo'], '0.115')
            self.assertIn('SPDXRef-Package-built-image', document['documentDescribes'])
            self.assertIn('SPDXRef-ImagePackage-fastapi', document['documentDescribes'])


if __name__ == '__main__':
    unittest.main()
