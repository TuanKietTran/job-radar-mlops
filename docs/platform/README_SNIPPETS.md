# README snippets for the platform docs

Note for the README owner: copy the block below into the README under a platform docs heading. Do not paste the screenshot images until the PNG files exist. Playwright is absent on this machine, so no PNG files were captured. The blocker is recorded in docs/platform/screenshots/BLOCKER.txt and the six pages are listed in docs/platform/screenshots/dry-run.txt. Run docs/platform/scripts/screenshots.py with Playwright present to write the PNG files at the paths below.

```markdown
## Platform docs

Architecture decisions, runbooks, data dictionary and diagrams live under docs/platform.

- Decisions: docs/platform/adr, 12 records numbered 0001 to 0012
- Runbooks: docs/platform/runbooks, local run, verify failure triage, release, incident response for a bad merge, onboarding a new worker
- Data dictionary: docs/platform/data-dictionary.md
- Diagrams: docs/platform/diagrams, context, container, component for the search API, deployment mapping
- Checks: python3 docs/platform/check.py

### Screenshots

![Guides index](docs/platform/screenshots/web__guides__dist__index.png)
![Guide article](docs/platform/screenshots/web__guides__dist__cau-truc-cv.png)
![Pages index](docs/platform/screenshots/web__pages-extra__site__index.png)
![Company page](docs/platform/screenshots/web__pages-extra__site__companies__an-nhien-systems.png)
![City page](docs/platform/screenshots/web__pages-extra__site__cities__ho-chi-minh-city.png)
![Industry page](docs/platform/screenshots/web__pages-extra__site__industries__software-development.png)
```
