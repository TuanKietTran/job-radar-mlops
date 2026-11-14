'''Tests for the container images in mlops/cicd.'''

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CICD = ROOT / 'mlops' / 'cicd'


class DockerfileTests(unittest.TestCase):
    def test_dockerfiles_have_pinned_base_and_non_root_user(self):
        for name in ('Dockerfile.api', 'Dockerfile.train'):
            with self.subTest(name=name):
                text = (CICD / name).read_text(encoding='utf-8')
                self.assertRegex(text, r'FROM python:3\.15\.\d+')
                self.assertIn('USER appuser', text)
                self.assertNotIn('USER root', text)
                self.assertIn('COPY', text)
                self.assertNotIn('SECRET', text)


if __name__ == '__main__':
    unittest.main()
