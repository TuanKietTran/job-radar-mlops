'''Write an SPDX JSON bill of materials for this repository.

Standard library only. Usage:

    python3 mlops/cicd/sbom.py [--root PATH] [--output PATH] [--base-image IMAGE]

The output lists the base image plus every file under the repository root
with a sha256 checksum each. The creation timestamp is fixed, so repeated
runs produce identical output for an unchanged tree.
'''

import argparse
import hashlib
import json
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


def build_sbom(root, base_image):
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
    args = parser.parse_args(argv)
    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).resolve().parents[2]
    if args.output:
        output = Path(args.output).resolve()
    else:
        output = root / 'mlops' / 'cicd' / 'sbom.spdx.json'
    document, count = build_sbom(root, args.base_image)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    try:
        display = output.relative_to(root)
    except ValueError:
        display = output
    print(f'sbom: wrote {display} with {count} files and base image {args.base_image}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
