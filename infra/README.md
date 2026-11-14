# Infrastructure

Terraform modules and root stacks for the job-radar platform, plus Kubernetes manifests and a Helm chart for the serving and training workloads. All state is local. No credentials, account numbers or endpoint addresses are stored in this tree.

## Layout

- `modules/aws-s3` - lakehouse bucket with versioning, encryption at rest and no public access
- `modules/aws-sagemaker` - model, endpoint configuration and endpoint
- `modules/aws-ecr` - repositories for the api and train images with scanning on push
- `modules/aws-iam` - least-privilege roles for train, serve and ingest
- `modules/azure-ml` - workspace, compute cluster and online endpoint
- `modules/databricks` - catalog, schema and cluster policy
- `aws`, `azure`, `databricks` - root stacks that compose the modules
- `k8s` - namespace, serving deployment, service and config map, train CronJob
- `helm/job-radar` - Helm chart for the same workloads

## Commands

Validate every stack and module, check formatting, manifests and credential patterns:

```
python3 infra/validate.py
```

Run the test suite from the repository root:

```
python3 -m unittest discover -s infra/tests
```

Validate one stack by hand (run `terraform init` first; it records provider selections in `.terraform.lock.hcl`):

```
cd infra/aws
terraform init -backend=false
terraform validate
terraform fmt -check
```

## Notes

- Root stacks use the local backend only. Providers are pinned in each stack and module.
- `tflint` and `helm` are not installed on the machine used to build this tree, so `infra/validate.py` records them as skipped and checks the Helm chart with the standard-library YAML sanity check instead.
- The train CronJob and the Helm chart use seed 42 for deterministic synthetic data.
