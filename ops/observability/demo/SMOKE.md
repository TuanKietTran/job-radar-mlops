# Demo smoke

Commands run from the worktree root:

```sh
DEMO_PORT=18080 .venv/bin/python -m ops.observability.demo.app
curl http://127.0.0.1:18080/
curl http://127.0.0.1:18080/jobs
curl http://127.0.0.1:18080/metrics
curl http://127.0.0.1:18080/nope
```

Observed output:

root: {"service": "job-radar-demo", "status": "ok"}
jobs: {"jobs": [{"id": "job-101", "title": "Backend engineer (.NET)", "company": "Northwind Logistics", "city": "Ho Chi Minh City", "salary_vnd": "35,000,000 - 45,000,000"}, {"id": "job-102", "title": "Fullstack engineer", "company": "Hanoi Data Works", "city": "Hanoi", "salary_vnd": "30,000,000 - 40,000,000"}, {"id": "job-103", "title": "Data engineer", "company": "Saigon Freight Systems", "city": "Ho Chi Minh City", "salary_vnd": "32,000,000 - 42,000,000"}], "total": 3}
unknown path status: 404
server log lines: 11

metrics excerpt:

```
# HELP http_requests_total Total HTTP requests.
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/",status="200"} 2.0
http_requests_total{method="GET",path="/jobs",status="200"} 1.0
# HELP http_errors_total Total HTTP error responses.
# TYPE http_errors_total counter
# HELP http_request_duration_seconds HTTP request latency in seconds.
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="0.01",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="0.025",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="0.05",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="0.1",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="0.25",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="0.5",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="1.0",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="2.5",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="5.0",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="10.0",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_bucket{le="+Inf",method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_count{method="GET",path="/",status="200"} 2.0
http_request_duration_seconds_sum{method="GET",path="/",status="200"} 0.00031120799758355133
http_request_duration_seconds_bucket{le="0.005",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="0.01",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="0.025",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="0.05",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="0.1",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="0.25",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="0.5",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="1.0",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="2.5",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="5.0",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="10.0",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_bucket{le="+Inf",method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_count{method="GET",path="/jobs",status="200"} 1.0
http_request_duration_seconds_sum{method="GET",path="/jobs",status="200"} 0.00012845800301874988
```
