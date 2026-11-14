# Pipeline tooling

This directory holds the continuous integration and delivery setup for
the repository: workflow files, offline checks, container builds, and
the bill of materials tool.

## Layout

- `.github/workflows/lint.yml` runs the offline checks on push and pull request.
- `.github/workflows/test.yml` runs the offline checks, the pipeline tests, and the API tests on push and pull request.
- `.github/workflows/build.yml` builds both container images and writes the bill of materials on push and pull request.
- `.github/workflows/train.yml` runs training on manual dispatch, or a dry-run guard when no training entry point is present.
- `.github/workflows/register.yml` runs registry checks on manual dispatch.
- `.github/workflows/deploy-canary.yml` builds the API image, checks health, and rolls back when the health check fails.
- `.github/workflows/rollback.yml` restores the previous stage on manual dispatch.
- `mlops/cicd/check.py` runs the same checks offline with the standard library only.
- `mlops/cicd/sbom.py` writes `sbom.spdx.json` with a sha256 checksum per file.
- `mlops/cicd/Dockerfile.api` and `mlops/cicd/Dockerfile.train` define the container images.
- `mlops/cicd/train-entry.sh` runs the training entry point when present, else the dry-run guard.
- `mlops/cicd/build.sh` builds both images and records the outcome.
- `mlops/cicd/tests/` holds the unit tests for the tooling in this directory.
- `.pre-commit-config.yaml` wires the offline checks into pre-commit.

## Commands

Run the offline checks from the repository root:

```
python3 mlops/cicd/check.py
```

Run the pipeline tests:

```
python3 -m unittest discover -s mlops/cicd/tests -v
```

Write the bill of materials:

```
python3 mlops/cicd/sbom.py
```

Build both container images:

```
sh mlops/cicd/build.sh
```

## Workflows

Every workflow uses `actions/checkout@v4` and Python 3.15, runs with
read-only repository permissions, and cancels an earlier run when a new
one starts. Nothing deploys on push. Training, registration, canary
deployment, and rollback run on manual dispatch only.

The training workflow runs `mlops/training/train.py` when that file is
present, else `mlops/training/main.py`, else a dry-run guard that exits
0 with a clear note. The registry workflow lists the registry
directory when it is present, else a guard that exits 0. The rollback
workflow restores `mlops/registry/previous-stage.txt` over
`mlops/registry/current-stage.txt` when both files are present, else a
guard that exits 0. The canary workflow starts the API, polls
`http://127.0.0.1:8000/health` for up to 60 seconds, and runs the same
restore step when the health check fails.

## Containers

Both images use `python:3.15.0-slim-bookworm` and run as a non-root
user. The API image copies `services/api` and starts the API on port
8000. The training image copies `mlops` and runs the training entry
point when it is present, else the dry-run guard. Neither image carries
credentials. The API requirements file is copied as it ships in the
repository.

## Bill of materials

`sbom.py` records the base image plus every file under the repository
root with a sha256 checksum each, in SPDX 2.3 JSON. The creation
timestamp is fixed, so repeated runs on an unchanged tree produce
identical output. The build workflow runs `syft` when it is present,
else `sbom.py`.

## Validation note

`pre-commit`, `actionlint`, and `tflint` are not installed on this
machine, so the workflows are validated by `check.py` plus review, not
by those tools. `check.py` performs the YAML sanity check with
line-based required-key checks because PyYAML is not installed. The
evidence log for the run that produced this directory is
`docs/evidence/mlops/cicd-run.log`.
