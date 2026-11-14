# Company directory pages

Static company directory and industry and city pages, generated from a data file. All companies are invented and all data is synthetic.

## Data

`data/companies.json` holds 30 invented companies. Each entry has a name, slug, industry, city, size band, founded year, short description and open roles count.

## Generate

Run `python3 generate.py` from this directory. It reads the data file and writes static HTML under `site/`: one directory index, one page per company, ten industry pages and ten city pages, plus `sitemap.xml` and `robots.txt`. The generator uses only the Python standard library and is deterministic.

## Test

Run `uvx pytest tests/test_pages.py -v` from this directory. The tests check page counts, page metadata, internal links, the sitemap and the robots file, and that the generator is re-runnable.
