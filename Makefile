# Minimal top-level Makefile. Delegates to mlops/Makefile from the repo root.
.PHONY: mlops-e2e verify crawl

mlops-e2e:
	$(MAKE) -f mlops/Makefile e2e

verify:
	python3 mlops/cicd/check.py
	python3 docs/platform/check.py
	python3 -m unittest discover mlops
	.venv/bin/pytest services/api/tests -q
	git diff --check

# Live crawl only. Refuses under CI inside run_live_crawl; with the
# core slice alone there are no live adapters yet (c-3..c-6 own
# those), so it exits 2 until one registers.
crawl:
	python3 -m services.crawler.fetch
