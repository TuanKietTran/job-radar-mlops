"""Validate the job-radar infrastructure tree.

Runs terraform validate and terraform fmt -check on every root stack and
module, checks Kubernetes manifests and the Helm chart for required keys,
and scans Terraform, YAML, Markdown, text and HCL files for credential
patterns. Uses only the standard library.

Usage:
    python3 infra/validate.py [--root DIR] [--only-credentials]
        [--skip-terraform] [--skip-manifests]

--root defaults to the directory holding this file. terraform runs share
one plugin cache under the user home so repeat runs do not re-download
providers. tflint runs when installed and is recorded as skipped when it
is not. helm template runs when helm is installed; otherwise the manifest
checks below stand in as the standard-library YAML sanity check.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

STACKS = ["aws", "azure", "databricks"]

SCAN_EXTENSIONS = {".tf", ".yaml", ".yml", ".md", ".txt", ".hcl"}
SKIP_DIRS = {".terraform", ".git", "__pycache__"}

CREDENTIAL_PATTERNS = [
    ("access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("password assignment", re.compile(r"(?i)password\s*[:=]")),
    ("secret assignment", re.compile(r"(?i)secret\s*[:=]")),
    ("private key block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----" )),
    ("aws secret key assignment", re.compile(r"(?i)aws_secret_access_key\s*[:=]")),
    ("private key assignment", re.compile(r"(?i)private[_ ]key\s*[:=]")),
]

K8S_CHECKS = {
    "namespace.yaml": ["apiVersion:", "kind: Namespace", "name: job-radar"],
    "serving-deployment.yaml": [
        "apiVersion:",
        "kind: Deployment",
        "replicas:",
        "containerPort: 8000",
        "livenessProbe:",
        "readinessProbe:",
    ],
    "serving-service.yaml": ["apiVersion:", "kind: Service", "port: 80"],
    "serving-configmap.yaml": ["apiVersion:", "kind: ConfigMap", "data:"],
    "train-cronjob.yaml": [
        "apiVersion:",
        "kind: CronJob",
        "schedule:",
        "restartPolicy: OnFailure",
        "42",
    ],
}

HELM_TEMPLATES = ["deployment.yaml", "service.yaml", "configmap.yaml", "cronjob.yaml"]


def terraform_env():
    env = dict(os.environ)
    cache = Path.home() / ".terraform.d" / "plugin-cache"
    env.setdefault("TF_PLUGIN_CACHE_DIR", str(cache))
    return env


def display_path(root, path):
    try:
        return str(Path(path).relative_to(root))
    except ValueError:
        return str(path)


def run(command, cwd, timeout):
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=terraform_env(),
    )
    return result


def terraform_check(directory, failures, root):
    label = display_path(root, directory)
    if shutil.which("terraform") is None:
        failures.append(f"{label}: terraform binary not found")
        return
    init = run(
        ["terraform", "init", "-backend=false", "-input=false", "-no-color"],
        directory,
        timeout=600,
    )
    if init.returncode != 0:
        failures.append(f"{label}: terraform init failed\n{init.stdout}{init.stderr}")
        return
    validate = run(["terraform", "validate", "-no-color"], directory, timeout=120)
    if validate.returncode != 0:
        failures.append(f"{label}: terraform validate failed\n{validate.stdout}{validate.stderr}")
        return
    fmt = run(["terraform", "fmt", "-check", "-no-color", "-diff"], directory, timeout=60)
    if fmt.returncode != 0:
        failures.append(f"{label}: terraform fmt -check failed\n{fmt.stdout}{fmt.stderr}")
        return
    print(f"[terraform] {label}: init ok, validate ok, fmt ok")


def tflint_check(root, directories, failures):
    if shutil.which("tflint") is None:
        print("[tflint] not installed, skipped")
        return
    for directory in directories:
        result = run(["tflint", "--no-color"], directory, timeout=120)
        if result.returncode != 0:
            failures.append(f"{display_path(root, directory)}: tflint failed\n{result.stdout}{result.stderr}")
        else:
            print(f"[tflint] {display_path(root, directory)}: ok")


def helm_check(root, failures):
    chart = root / "helm" / "job-radar"
    if shutil.which("helm") is None:
        print("[helm] not installed, skipped; stdlib YAML sanity check used instead")
        return
    result = run(
        ["helm", "template", "job-radar", str(chart), "--namespace", "job-radar"],
        root,
        timeout=120,
    )
    if result.returncode != 0:
        failures.append(f"helm template failed\n{result.stdout}{result.stderr}")
    else:
        print("[helm] helm template ok")


def manifest_check(root, failures):
    before = len(failures)
    k8s = root / "k8s"
    checked = 0
    for name, required in K8S_CHECKS.items():
        path = k8s / name
        if not path.is_file():
            failures.append(f"manifest missing: {display_path(root, path)}")
            continue
        text = path.read_text(encoding="utf-8")
        checked += 1
        for key in required:
            if key not in text:
                failures.append(f"{display_path(root, path)}: missing required key {key!r}")
    chart = root / "helm" / "job-radar"
    chart_yaml = chart / "Chart.yaml"
    if not chart_yaml.is_file():
        failures.append(f"chart missing: {display_path(root, chart_yaml)}")
    else:
        text = chart_yaml.read_text(encoding="utf-8")
        checked += 1
        for key in ["apiVersion: v2", "name: job-radar", "version: 0.1.0"]:
            if key not in text:
                failures.append(f"{display_path(root, chart_yaml)}: missing required key {key!r}")
    values = chart / "values.yaml"
    if not values.is_file():
        failures.append(f"chart missing: {display_path(root, values)}")
    else:
        text = values.read_text(encoding="utf-8")
        checked += 1
        for key in ["replicaCount:", "repository:", "schedule:"]:
            if key not in text:
                failures.append(f"{display_path(root, values)}: missing required key {key!r}")
    templates = chart / "templates"
    for name in HELM_TEMPLATES:
        path = templates / name
        if not path.is_file():
            failures.append(f"chart template missing: {display_path(root, path)}")
            continue
        text = path.read_text(encoding="utf-8")
        checked += 1
        if "{{" not in text:
            failures.append(f"{display_path(root, path)}: template has no template expressions")
    notes = templates / "NOTES.txt"
    if not notes.is_file() or not notes.read_text(encoding="utf-8").strip():
        failures.append(f"chart notes missing or empty: {display_path(root, notes)}")
    else:
        checked += 1
    if len(failures) == before:
        print(f"[manifests] ok ({checked} files checked)")


def credential_scan(root, failures):
    scanned = 0
    hits = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        scanned += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            for label, pattern in CREDENTIAL_PATTERNS:
                if pattern.search(line):
                    hits += 1
                    failures.append(f"{display_path(root, path)}:{number}: credential pattern ({label}): {line.strip()}")
    if hits == 0:
        print(f"[credentials] ok ({scanned} files scanned, no hits)")
    return scanned


def terraform_dirs(root):
    directories = []
    for name in STACKS:
        path = root / name
        if path.is_dir():
            directories.append(path)
    modules = root / "modules"
    if modules.is_dir():
        directories.extend(sorted(p for p in modules.iterdir() if p.is_dir()))
    return directories


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the infrastructure tree.")
    parser.add_argument("--root", default=None, help="Infra root, defaults to this file's directory.")
    parser.add_argument("--only-credentials", action="store_true", help="Run only the credential scan.")
    parser.add_argument("--skip-terraform", action="store_true", help="Skip terraform checks.")
    parser.add_argument("--skip-manifests", action="store_true", help="Skip manifest checks.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent
    failures = []

    if shutil.which("terraform") is not None:
        version = run(["terraform", "version", "-no-color"], root, timeout=30)
        print(version.stdout.splitlines()[0] if version.stdout else "terraform: version unknown")
    else:
        print("terraform: not installed")

    if args.only_credentials:
        credential_scan(root, failures)
    else:
        directories = terraform_dirs(root)
        if not args.skip_terraform:
            for directory in directories:
                terraform_check(directory, failures, root)
            tflint_check(root, directories, failures)
            helm_check(root, failures)
        if not args.skip_manifests:
            manifest_check(root, failures)
        credential_scan(root, failures)

    if failures:
        print(f"validate.py: FAIL ({len(failures)} checks failed)")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("validate.py: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
