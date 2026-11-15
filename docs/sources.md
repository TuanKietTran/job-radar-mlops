# Job Radar sources

Evaluated 2026-11-15. Scope: 10 providers, 3,000+ real live listings each, crawled live, not fixtures. Method: sitemap index to job URLs, per-job JobPosting JSON-LD, shared fetch layer with disk cache, robots.txt honored, 2 seconds or more per host, stop on 403 or 429 with no retries. Counts below are sitemap or API URL counts, not crawled records yet. Real crawled counts go in status/provider-counts.md. If a provider cannot reach 3,000 legally, ship what it has and say so, never pad with fixtures or duplicates.

Policy: crawling is allowed and the ToS risk for Vietnamese boards is accepted, with technical hygiene still required: honor robots.txt, honest generic user agent, 2 seconds or more per host, stop on 403 or 429, no login, no captcha solving, no IP or fingerprint evasion, public pages only, keep the original posting URL, no personal data beyond what the posting shows. LinkedIn: check robots.txt first, crawl only pages robots permits, else mark disabled-by-policy and cover via ATS APIs and employer career pages. Never ingest jobnexus.io.vn itself or its Enterprise ATS listings. Every record comes from the public pages of each provider.

## Chosen 10

| Provider | Source | Job URLs | Robots | Notes |
| --- | --- | --- | --- | --- |
| ITviec | Sitemap | 597 | Allows, except /subscriptions/new | Adapter exists. Below target, honest count. |
| Vieclam24h | Sitemap | 17,789 | Allows | Adapter merged. |
| RemoteOK | JSON API | 97 | Public API | Merged. Below target, honest count. |
| CareerViet | Sitemap | 16,758 | Does not disallow job paths | Job pages live under /vi/tim-viec-lam/ and /en/search-job/. |
| Timviec365 | Sitemap | 13,165 | Allow / | |
| Ybox | Sitemap | ~39,000 fresh | Disallows only /bookmarked, /histories | Fresh range is shards 125-135, all lastmod 2026. |
| Hoteljob | Sitemap | 176,021 | Allow / | 36 shards counted. 4 shards (p20, p32, p33, p34) return HTTP 500, so up to ~196,021 if they recover. |
| TopCV | Sitemap | ~39,352 inferred | Allows job pages | CONDITIONAL: curl gets Cloudflare 403, so the crawl needs a fetch route that does not bypass blocks. |
| Vieclamtot | Sitemap | 15,985 | Allow / | JobPosting verified on 3 of 3 sampled pages. CONDITIONAL: curl gets Cloudflare 403, same caveat. |
| Greenhouse | JSON API | 3,595 | Public boards API | ATS slot. 13 company boards verified in the ATS evaluation round, tokens re-verified in follow-up ATS verification. |

## Not chosen

| Provider | Reason |
| --- | --- |
| VietnamWorks | No listing source: robots.txt 404, sitemap 404, rss 403. Only 5 featured jobs visible, detail pages carry no JobPosting. |
| JobsGO | Adapter in progress in its own worker chat. Sitemap 403 via curl, volume unverified, JobPosting unconfirmed. Not counted yet. |
| TopDev | Unreachable by curl: 3 connection timeouts, no verified count. |
| CareerLink | sitemap.xml 404, sitemap_index.xml 301, no usable sitemap source. |
| 123job | Sitemap holds 0 job URLs, 199 browse and wiki pages only. |
| Tuyencongnhan | sitemap_jobs.xml reachable, but only 309 job URLs, below target. |
| Glints | Sitemap returns a firewall page, no volume. |
| Indeed VN | sitemap.xml 404, volume unverified. |
| LinkedIn | robots.txt Disallow / for all agents. Disabled-by-policy, cover via ATS and employer career pages. |
| NodeFlair | Sitemap 403 Cloudflare, no volume via curl. |
| We Work Remotely | Sitemap 403, merged adapter is RSS only with 25 items, below target. |
| Ashby | 1,217 jobs across 4 tokens so far, below target. More tokens may add in follow-up ATS verification. |
| Lever | 87 jobs so far, below target. |

## Notes

- TopCV total is inferred from the 200-per-shard pattern across 197 shards, with 4 shards counted by browser and tail shard 196 at 152. Exact total still unverified.
- Hoteljob total counts 36 working shards. The 4 erroring shards return HTTP 500 on recheck, not empty pages.
- ITviec and RemoteOK are in per commander decision although below 3,000. Their counts are reported honestly.
- ATS totals come from the ATS evaluation round. Greenhouse crosses 3,000, Ashby and Lever do not yet.
