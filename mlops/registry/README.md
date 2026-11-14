# Model registry

Versioned model artifacts and stages. Model files are plain JSON params, never pickle.

## Layout

Each version lives at models/<model>/<version>/ and holds model.json, metadata.json, card.md, stage.txt, and metrics.json when an evaluation ran.

## Stages and guards

Stages are dev, staging, production and archived. Allowed moves are dev to staging or archived, staging to production or archived, and production to archived.

- A version cannot move to staging without metrics.
- A version cannot move to production without a model card and an evaluation run.

Register starts a version at dev. Promote moves it along the allowed path and records the deployment.

## Commands

```
python3 -m mlops.registry.registry register --model salary --artifact /tmp/b4-e2e/salary --metrics /tmp/b4-e2e/salary/metrics.json --root /tmp/b4-e2e/models --metadata-db /tmp/b4-e2e/metadata.db --experiments /tmp/b4-e2e/experiments.jsonl
python3 -m mlops.registry.registry promote --model salary --version v1 --to staging --root /tmp/b4-e2e/models --metadata-db /tmp/b4-e2e/metadata.db
python3 -m mlops.registry.registry promote --model salary --version v1 --to production --root /tmp/b4-e2e/models --metadata-db /tmp/b4-e2e/metadata.db
python3 -m mlops.registry.registry list --root /tmp/b4-e2e/models
python3 -m mlops.registry.registry load --model salary --version v1 --root /tmp/b4-e2e/models
```

Register accepts --metrics as a metrics JSON file or a directory holding metrics.json, and --params as an optional JSON file with extra params. Without --root, the registry root defaults to mlops/registry/models. List accepts --model to show one model only. Load prints the model kind, model name, version, stage and artifact path.

## Metadata

Register and promote write to the SQLite metadata store and experiments.jsonl when --metadata-db and --experiments are given. List the store with:

```
python3 -m mlops.metadata.store list-runs --db /tmp/b4-e2e/metadata.db
python3 -m mlops.metadata.store list-models --db /tmp/b4-e2e/metadata.db
python3 -m mlops.metadata.store list-deployments --db /tmp/b4-e2e/metadata.db
```

## Tests

```
python3 -m unittest discover -s mlops/tests
```
