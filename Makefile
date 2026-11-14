# Job Radar Makefile. Run from the repo root.
.PHONY: help setup up down test verify screenshots smoke mlops-e2e hygiene clean

PY := python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
COMPOSE := docker compose

help:
	@echo 'Targets: setup, up, down, test, verify, screenshots, smoke, mlops-e2e, hygiene, clean'
	@echo '  setup       create .venv and install service requirements'
	@echo '  up          start api, ai, web and ingest with docker compose'
	@echo '  down        stop the compose stack'
	@echo '  test        run mlops unit tests and service tests'
	@echo '  verify      run checks, tests, hygiene and smoke checks'
	@echo '  screenshots capture docs/evidence/screenshots with scripts/screenshots.py'
	@echo '  smoke       run salary, ingest and api smoke checks'
	@echo '  mlops-e2e   run the mlops end-to-end script'
	@echo '  hygiene     run scripts/hygiene.sh'
	@echo '  clean       remove generated data, never source'

setup: $(VENV_PY)

$(VENV_PY):
	$(PY) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r services/api/requirements.txt -r services/ai/requirements.txt

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down --remove-orphans

test: setup
	$(PY) -m unittest discover mlops
	$(VENV_PY) -m pytest services -q

verify: setup hygiene
	$(PY) mlops/cicd/check.py
	$(PY) docs/platform/check.py
	$(PY) -m unittest discover mlops
	$(VENV_PY) -m pytest services/api/tests -q
	$(MAKE) smoke
	git diff --check

smoke: setup
	$(VENV_PY) -m services.salary.cli --gross 30000000 --dependents 1
	$(VENV_PY) scripts/smoke.py

screenshots:
	$(PY) scripts/screenshots.py --dry-run

mlops-e2e:
	$(MAKE) -f mlops/Makefile e2e

hygiene:
	bash scripts/hygiene.sh

clean:
	$(COMPOSE) down --remove-orphans --volumes
	rm -rf mlops/data/lake mlops/data/synthetic mlops/features/offline.db mlops/features/online.db mlops/registry/models mlops/metadata mlops/training/artifacts mlops/monitoring/alerts docs/evidence/mlops/e2e-*.log
