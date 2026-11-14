# ADR 0012: Deployment mapping to AWS, Azure and Databricks

## Status

Proposed

## Context

No deployment code exists on main at 7ef6012. The only cloud mention on main is aws as a skill string in the synthetic data generator at mlops/data/generate.py. Terraform, Kubernetes manifests and a Helm chart exist on branch infra/terraform at 8bdba4d, unmerged, with root stacks under infra/aws, infra/azure and infra/databricks, modules for aws-s3, aws-sagemaker, aws-ecr, aws-iam and azure-ml, and a Helm chart for the job radar service. No deployment from that branch has been recorded against main.

## Decision

Proposed. Map the platform to three clouds: AWS for object storage, model serving and the container registry, Azure for the managed ML workspace, and Databricks for training and evaluation workloads, with the service itself deployed from the Helm chart onto Kubernetes. The mapping stays proposed until the infra branch is merged and a deployment has run.

## Consequences

- Each cloud holds the part its module names cover, so no single cloud is required to run the whole platform.
- The mapping is a plan, not a deployment, so no endpoint or address can be quoted from it.
- Merging the infra branch does not deploy anything by itself, so the first deployment needs its own recorded run.
- The local observability stack in ADR 0010 stays local until a deployment decision covers it, so production observation is still open.
