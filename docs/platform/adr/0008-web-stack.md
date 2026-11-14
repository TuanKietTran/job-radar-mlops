# ADR 0008: Web stack

## Status

Decided

## Context

web/pages-extra/generate.py reads data/companies.json and writes a static site under site/ using html, json and pathlib from the standard library.

There is no web/tools directory and no JavaScript framework or server-side rendering in the repo. Pages are plain HTML and CSS, with a small search page backed by search.json.

## Decision

Keep the web pages as static output from standard-library Python generators. No web framework, no build tool and no runtime server for the pages themselves. The search API stays a separate service.

## Consequences

- Pages build with python3 and no install step, and the output can be served from any static host.
- The pages-extra generator owns its input, companies.json, so a content change rebuilds only its own pages.
- Interactive behaviour is limited to what static pages and search.json support, so a feature needing a server must go through the search API instead.
- The base URL in pages-extra is the example placeholder https://job-radar.example, so a real host must replace it before publish.
