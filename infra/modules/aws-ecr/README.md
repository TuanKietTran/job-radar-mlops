# aws-ecr

Repositories for the api and train images, with scanning on push and AES256 encryption at rest.

## Inputs

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `project` | string | `job-radar` | Project name used as a prefix for repository names |
| `environment` | string | `dev` | Deployment environment: dev, staging or prod |
| `repositories` | list(string) | `["api", "train"]` | Repository names, one per image |
| `scan_on_push` | bool | `true` | Scan each image for vulnerabilities on push |
| `force_delete` | bool | `false` | Allow Terraform to delete a repository holding images |
| `tags` | map(string) | `{}` | Tags applied to the repositories |

## Outputs

| Name | Description |
| --- | --- |
| `repository_urls` | Repository URLs keyed by repository name |
| `repository_arns` | Repository ARNs keyed by repository name |
| `repository_names` | Repository names keyed by repository name |

## Notes

- Tags are immutable, so a pushed tag cannot be overwritten.
- The lifecycle policy keeps the latest 10 images in each repository.
