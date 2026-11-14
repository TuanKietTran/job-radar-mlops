# azure-ml

Workspace, training compute cluster and online endpoint.

## Inputs

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `project` | string | `job-radar` | Project name used as a prefix for resource names |
| `environment` | string | `dev` | Deployment environment: dev, staging or prod |
| `location` | string | `southeastasia` | Azure region for the workspace |
| `resource_group_name` | string | - | Name of the resource group that holds the workspace |
| `storage_account_id` | string | - | ID of the storage account for the workspace |
| `key_vault_id` | string | - | ID of the key vault for the workspace |
| `application_insights_id` | string | - | ID of the Application Insights resource for the workspace |
| `compute_vm_size` | string | `Standard_DS3_v2` | VM size for the training compute cluster |
| `compute_min_nodes` | number | `0` | Minimum nodes for the training compute cluster |
| `compute_max_nodes` | number | `2` | Maximum nodes for the training compute cluster |
| `tags` | map(string) | `{}` | Tags applied to the workspace resources |

## Outputs

| Name | Description |
| --- | --- |
| `workspace_id` | ID of the machine learning workspace |
| `workspace_name` | Name of the machine learning workspace |
| `compute_cluster_name` | Name of the training compute cluster |
| `endpoint_name` | Name of the online endpoint |

## Notes

- The workspace, storage account, key vault and Application Insights resource are separate inputs, so this module holds no identifiers of its own.
- The compute cluster scales to zero nodes when idle and back up to the maximum while training runs.
- The online endpoint uses token auth. It is provisioned with `azapi_resource`, because the `azurerm` provider has no native online endpoint resource.
