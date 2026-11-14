# Run from the repo root. Targets use repo-root relative paths.
.PHONY: test e2e serve clean

test:
	python3 -m unittest discover -s mlops/tests

e2e:
	bash mlops/scripts/e2e.sh

# Serve needs a registered production model first, see the README.
serve:
	python3 -m mlops.serving.app

# Clean removes generated data only, never source.
clean:
	rm -rf mlops/data/lake mlops/data/synthetic mlops/features/offline.db mlops/features/online.db mlops/registry/models mlops/metadata mlops/training/artifacts mlops/monitoring/alerts docs/evidence/mlops/e2e-*.log
