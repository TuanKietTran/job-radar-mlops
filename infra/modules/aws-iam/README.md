# aws-iam

Least-privilege roles for train, serve and ingest. Every policy names its actions and its resources. No policy uses a wildcard action or a wildcard resource.

## Inputs

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `project` | string | `job-radar` | Project name used as a prefix for role names |
| `environment` | string | `dev` | Deployment environment: dev, staging or prod |
| `lakehouse_bucket_arn` | string | - | ARN of the lakehouse bucket |
| `api_repository_arn` | string | - | ARN of the api image repository |
| `train_repository_arn` | string | - | ARN of the train image repository |
| `endpoint_name` | string | `""` | Name of the SageMaker endpoint the serve role may invoke. Defaults to `<project>-<environment>-endpoint` |
| `tags` | map(string) | `{}` | Tags applied to the roles and policies |

## Outputs

| Name | Description |
| --- | --- |
| `train_role_arn` | ARN of the train role |
| `serve_role_arn` | ARN of the serve role |
| `ingest_role_arn` | ARN of the ingest role |
| `train_role_name` | Name of the train role |
| `serve_role_name` | Name of the serve role |
| `ingest_role_name` | Name of the ingest role |

## Roles

- `train` - assumed by SageMaker. Lists the lakehouse bucket, reads and writes its objects, pulls the train image.
- `serve` - assumed by SageMaker. Reads lakehouse objects, pulls the api image, invokes one endpoint by its exact ARN.
- `ingest` - assumed by the ingest task. Lists the lakehouse bucket and writes its objects. It has no read access to objects and no image access.

The endpoint ARN is built from the current caller identity and region, so no account number is written in this tree.
