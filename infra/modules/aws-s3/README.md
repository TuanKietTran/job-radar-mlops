# aws-s3

Lakehouse bucket with versioning, encryption at rest and no public access.

## Inputs

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `bucket_prefix` | string | - | Prefix for the lakehouse bucket name |
| `environment` | string | `dev` | Deployment environment: dev, staging or prod |
| `enable_versioning` | bool | `true` | Enable versioning on the bucket |
| `force_destroy` | bool | `false` | Allow Terraform to delete a non-empty bucket |
| `tags` | map(string) | `{}` | Tags applied to the bucket |

## Outputs

| Name | Description |
| --- | --- |
| `bucket_id` | Name of the lakehouse bucket |
| `bucket_arn` | ARN of the lakehouse bucket |
| `bucket_domain_name` | Domain name of the lakehouse bucket |

## Notes

- Encryption uses AES256 server-side encryption.
- Public access is blocked on all four settings.
- Noncurrent versions expire after 90 days.
