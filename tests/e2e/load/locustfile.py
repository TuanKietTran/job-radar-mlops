import random

from locust import HttpUser, between, task

QUERIES = ['python', 'java', 'react', 'data', 'ky su']
JOB_IDS = ['job-01', 'job-02', 'job-03', 'job-07', 'job-14']


class JobSearchUser(HttpUser):
    wait_time = between(1, 2)
    host = 'http://127.0.0.1:8000'

    def on_start(self):
        self.client.get('/health')

    @task(3)
    def search(self):
        self.client.get(
            '/api/jobs', params={'q': random.choice(QUERIES), 'page_size': 20}
        )

    @task(1)
    def job_detail(self):
        self.client.get('/api/jobs/job-01')

    @task(1)
    def filters(self):
        self.client.get('/api/filters')
