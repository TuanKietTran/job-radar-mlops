"""Crawler package.

The live fetch layer and per-source adapters belong to the crawler core
slice. This package also holds the crawl entrypoint, which keeps live
crawling separate from the fixture mode used by every test and verify
target.
"""
