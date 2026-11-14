# Minimal top-level Makefile. Delegates to mlops/Makefile from the repo root.
.PHONY: mlops-e2e

mlops-e2e:
	$(MAKE) -f mlops/Makefile e2e
