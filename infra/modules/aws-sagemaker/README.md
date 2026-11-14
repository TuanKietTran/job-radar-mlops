# aws-sagemaker

Model, endpoint configuration and endpoint for serving.

## Inputs

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `project` | string | `job-radar` | Project name used as a prefix for resource names |
| `environment` | string | `dev` | Deployment environment: dev, staging or prod |
| `model_image` | string | - | Container image for the model |
| `model_data_url` | string | `null` | S3 URL of the model artefacts. Null when the image holds the model |
| `instance_type` | string | `ml.t3.medium` | SageMaker instance type for the endpoint |
| `endpoint_instance_count` | number | `1` | Number of endpoint instances |
| `execution_role_arn` | string | - | ARN of the role SageMaker assumes to run the model |
| `tags` | map(string) | `{}` | Tags applied to the SageMaker resources |

## Outputs

| Name | Description |
| --- | --- |
| `model_name` | Name of the SageMaker model |
| `endpoint_name` | Name of the SageMaker endpoint |
| `endpoint_arn` | ARN of the SageMaker endpoint |

## Notes

- The endpoint name is `<project>-<environment>-endpoint`.
- The instance type is a variable so each environment can size the endpoint on its own.
