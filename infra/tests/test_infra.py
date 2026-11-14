"""Tests for the job-radar infrastructure tree. Standard library only.

Run from the repository root:
    python3 -m unittest discover -s infra/tests
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA = REPO_ROOT / "infra"

STACKS = ["aws", "azure", "databricks"]

MODULES = [
    "aws-s3",
    "aws-sagemaker",
    "aws-ecr",
    "aws-iam",
    "azure-ml",
    "databricks",
]

REQUIRED_FILES = [
    "modules/aws-s3/main.tf",
    "modules/aws-s3/variables.tf",
    "modules/aws-s3/outputs.tf",
    "modules/aws-s3/README.md",
    "modules/aws-sagemaker/main.tf",
    "modules/aws-sagemaker/variables.tf",
    "modules/aws-sagemaker/outputs.tf",
    "modules/aws-sagemaker/README.md",
    "modules/aws-ecr/main.tf",
    "modules/aws-ecr/variables.tf",
    "modules/aws-ecr/outputs.tf",
    "modules/aws-ecr/README.md",
    "modules/aws-iam/main.tf",
    "modules/aws-iam/variables.tf",
    "modules/aws-iam/outputs.tf",
    "modules/aws-iam/README.md",
    "modules/azure-ml/main.tf",
    "modules/azure-ml/variables.tf",
    "modules/azure-ml/outputs.tf",
    "modules/azure-ml/README.md",
    "modules/databricks/main.tf",
    "modules/databricks/variables.tf",
    "modules/databricks/outputs.tf",
    "modules/databricks/README.md",
    "aws/main.tf",
    "azure/main.tf",
    "databricks/main.tf",
    ".tflint.hcl",
    "k8s/namespace.yaml",
    "k8s/serving-deployment.yaml",
    "k8s/serving-service.yaml",
    "k8s/serving-configmap.yaml",
    "k8s/train-cronjob.yaml",
    "helm/job-radar/Chart.yaml",
    "helm/job-radar/values.yaml",
    "helm/job-radar/templates/_helpers.tpl",
    "helm/job-radar/templates/deployment.yaml",
    "helm/job-radar/templates/service.yaml",
    "helm/job-radar/templates/configmap.yaml",
    "helm/job-radar/templates/cronjob.yaml",
    "helm/job-radar/templates/NOTES.txt",
    "validate.py",
    "README.md",
]


def run(command, cwd, timeout=900):
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def init_and_validate(directory):
    init = run(
        ["terraform", "init", "-backend=false", "-input=false", "-no-color"],
        directory,
    )
    assert init.returncode == 0, f"{directory}: terraform init failed\n{init.stdout}{init.stderr}"
    validate = run(["terraform", "validate", "-no-color"], directory, timeout=120)
    assert validate.returncode == 0, (
        f"{directory}: terraform validate failed\n{validate.stdout}{validate.stderr}"
    )


class TestInfraFiles(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [name for name in REQUIRED_FILES if not (INFRA / name).is_file()]
        self.assertEqual(missing, [])

    def test_iam_has_no_wildcard(self):
        text = (INFRA / "modules" / "aws-iam" / "main.tf").read_text(encoding="utf-8")
        self.assertNotIn('"*"', text)
        self.assertNotIn("'*'", text)

    def test_no_banned_tokens_in_tree(self):
        key_pattern = re.compile(r"AKIA[0-9A-Z]{16}")
        for base in (INFRA, REPO_ROOT / "docs" / "evidence" / "mlops"):
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*")):
                if not path.is_file():
                    continue
                if '.terraform' in path.parts or '.git' in path.parts or '__pycache__' in path.parts:
                    continue
                if path.suffix in ('.py', '.pyc', '.pyo'):
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn('/Us' + 'ers/', text, f"{path} holds a home path")
                self.assertIsNone(key_pattern.search(text), f"{path} holds an access key id")


class TestTerraform(unittest.TestCase):
    def test_terraform_validate_stacks(self):
        for name in STACKS:
            with self.subTest(stack=name):
                init_and_validate(INFRA / name)

    def test_terraform_validate_modules(self):
        for name in MODULES:
            with self.subTest(module=name):
                init_and_validate(INFRA / "modules" / name)

    def test_terraform_fmt_clean(self):
        result = run(
            ["terraform", "fmt", "-check", "-recursive", "-no-color", "-diff"],
            INFRA,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, f"terraform fmt -check failed\n{result.stdout}{result.stderr}")


class TestValidateScript(unittest.TestCase):
    def test_validate_py_passes_on_clean_tree(self):
        result = run([sys.executable, str(INFRA / "validate.py")], REPO_ROOT, timeout=1200)
        self.assertEqual(result.returncode, 0, f"validate.py failed\n{result.stdout}{result.stderr}")
        self.assertIn("validate.py: PASS", result.stdout)

    def test_validate_py_fails_on_fixture_with_fake_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "infra" / "modules" / "fake"
            fixture.mkdir(parents=True)
            (fixture / "main.tf").write_text(
                'variable "example" {\n  default = "AKIAIOSFODNN7EXAMPLE"\n}\n',
                encoding="utf-8",
            )
            result = run(
                [
                    sys.executable,
                    str(INFRA / "validate.py"),
                    "--root",
                    str(Path(tmp) / "infra"),
                    "--only-credentials",
                ],
                REPO_ROOT,
                timeout=120,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AKIAIOSFODNN7EXAMPLE", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
