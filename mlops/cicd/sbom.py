'''Write an SPDX JSON bill of materials for this repository.

Standard library only. Usage:

    python3 mlops/cicd/sbom.py [--root PATH] [--output PATH] [--base-image IMAGE] [--image IMAGE]

The output lists the base image plus every file under the repository root
with a sha256 checksum each. The creation timestamp is fixed, so repeated
runs produce identical output for an unchanged tree. With --image, the python
packages installed in the built image (via docker run pip list) are listed
as packages too, plus the built image with its image id.
'''

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {'.git', '.venv', '__pycache__', '.tox', 'node_modules'}
CREATED = '2026-01-01T00:00:00Z'


def _iter_files(root):
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name == 'sbom.spdx.json':
            continue
        yield path, rel


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _pip_packages(text):
    packages = []
    try:
        entries = json.loads(text)
    except ValueError:
        return packages
    for entry in entries:
        name = entry.get('name')
        version = entry.get('version')
        if name and version:
            packages.append((name, version))
    return sorted(packages)


def _image_pip_packages(image):
    result = subprocess.run(
        ['docker', 'run', '--rm', image, 'python3', '-m', 'pip', 'list', '--format=json'],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError('pip list failed in image ' + image + ': ' + result.stderr.strip())
    return _pip_packages(result.stdout)


def _image_id(image):
    result = subprocess.run(
        ['docker', 'image', 'inspect', '-f', '{{.Id}}', image],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError('image inspect failed for ' + image + ': ' + result.stderr.strip())
    return result.stdout.strip()


def build_sbom(root, base_image, image=None, image_packages=None, image_id=None):
    packages = []
    described = []
    base_id = 'SPDXRef-Package-base-image'
    version = base_image.rsplit(':', 1)[-1] if ':' in base_image else 'NOASSERTION'
    packages.append({
        'SPDXID': base_id,
        'name': base_image,
        'versionInfo': version,
        'supplier': 'NOASSERTION',
        'downloadLocation': 'NOASSERTION',
        'filesAnalyzed': False,
    })
    described.append(base_id)
    if image is not None:
        built_id = 'SPDXRef-Package-built-image'
        packages.append({
            'SPDXID': built_id,
            'name': image,
            'versionInfo': image_id or 'NOASSERTION',
            'supplier': 'NOASSERTION',
            'downloadLocation': 'NOASSERTION',
            'filesAnalyzed': False,
        })
        described.append(built_id)
    for name, version in image_packages or []:
        package_id = 'SPDXRef-ImagePackage-' + re.sub(r'[^A-Za-z0-9.-]', '-', name)
        packages.append({
            'SPDXID': package_id,
            'name': name,
            'versionInfo': version,
            'supplier': 'NOASSERTION',
            'downloadLocation': 'NOASSERTION',
            'filesAnalyzed': False,
        })
        described.append(package_id)
    count = 0
    for path, rel in _iter_files(root):
        count += 1
        package_id = f'SPDXRef-File-{count}'
        packages.append({
            'SPDXID': package_id,
            'name': rel.as_posix(),
            'versionInfo': 'NOASSERTION',
            'supplier': 'NOASSERTION',
            'downloadLocation': 'NOASSERTION',
            'filesAnalyzed': False,
            'checksums': [
                {'algorithm': 'SHA256', 'checksumValue': _sha256(path)},
            ],
        })
        described.append(package_id)
    document = {
        'spdxVersion': 'SPDX-2.3',
        'dataLicense': 'CC0-1.0',
        'SPDXID': 'SPDXRef-DOCUMENT',
        'name': 'job-radar-mlops',
        'documentNamespace': 'urn:job-radar-mlops:sbom',
        'creationInfo': {
            'created': CREATED,
            'creators': ['Tool: mlops-cicd-sbom'],
        },
        'packages': packages,
        'documentDescribes': described,
    }
    return document, count


def main(argv=None):
    parser = argparse.ArgumentParser(description='Write an SPDX JSON bill of materials.')
    parser.add_argument('--root', default=None, help='Repository root. Defaults to the parent of mlops.')
    parser.add_argument('--output', default=None, help='Output path. Defaults to mlops/cicd/sbom.spdx.json under the root.')
    parser.add_argument('--base-image', default='python:3.15.0-slim-bookworm', help='Base image recorded in the bill of materials.')
    parser.add_argument('--image', default=None, help='Built image to list python packages from with docker run pip list.')
    args = parser.parse_args(argv)
    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parents[2]
    if args.output:
        output = Path(args.output).resolve()
    else:
        output = root / 'mlops' / 'cicd' / 'sbom.spdx.json'
    image_packages = None
    image_id = None
    if args.image:
        image_packages = _image_pip_packages(args.image)
        image_id = _image_id(args.image)
    document, count = build_sbom(root, args.base_image, image=args.image, image_packages=image_packages, image_id=image_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    try:
        display = output.relative_to(root)
    except ValueError:
        display = output
    if image_packages is None:
        print(f'sbom: wrote {display} with {count} files and base image {args.base_image}')
    else:
        print(f'sbom: wrote {display} with {count} files and {len(image_packages)} image packages from {args.image}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
