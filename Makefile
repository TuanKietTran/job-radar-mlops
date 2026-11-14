# Minimal top-level Makefile. Delegates to mlops/Makefile from the repo root.
.PHONY: mlops-e2e verify crawl crawl-dry-run

mlops-e2e:
	$(MAKE) -f mlops/Makefile e2e

verify:
	python3 mlops/cicd/check.py
	python3 docs/platform/check.py
	python3 -m unittest discover mlops
	.venv/bin/pytest services/api/tests -q
	git diff --check

# Fixture mode is the default: verify and mlops-e2e use recorded fixtures
# only and never touch the network. Live crawling is opt-in only, via
# `make crawl`, which refuses to run when CI is set and is never called
# from CI or from verify / mlops-e2e. `make crawl --dry-run` is make's own
# dry-run flag, so it lists the steps below without fetching anything.
# `make crawl-dry-run` runs the same step list for real, also offline.
crawl:
	@echo "STEP 1: check robots.txt for each source, never fetch disallowed paths"
	@echo "STEP 2: fetch with the shared fetch layer and an honest generic User-Agent"
	@echo "STEP 3: serve a cached response from disk when one is present"
	@echo "STEP 4: rate limit, at least 2 seconds between requests per host"
	@echo "STEP 5: stop a source for the run on a 403 or 429, with no retries against it"
	@echo "STEP 6: normalize raw records with services.ingest.normalize"
	@echo "STEP 7: dedupe across sources with services.ingest.dedupe, then feed the pipeline"
	python3 services/crawler/crawl.py

crawl-dry-run:
	python3 services/crawler/crawl.py --dry-run
