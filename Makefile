# Minimal top-level Makefile. Delegates to mlops/Makefile from the repo root.
.PHONY: mlops-e2e verify

mlops-e2e:
	$(MAKE) -f mlops/Makefile e2e

verify:
	python3 mlops/cicd/check.py
	python3 docs/platform/check.py
	python3 -m unittest discover mlops
	.venv/bin/pytest services/api/tests -q
	git diff --check
