# databricks

Workspace-level catalog, schema and cluster policy.

## Inputs

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `project` | string | `job-radar` | Project name used as a prefix for the cluster policy name |
| `environment` | string | `dev` | Deployment environment: dev, staging or prod |
| `catalog_name` | string | `job_radar` | Name of the catalog |
| `schema_name` | string | `gold` | Name of the schema |
| `spark_version` | string | `15.4.x-scala2.12` | Spark version pinned by the cluster policy |
| `node_type_id` | string | `Standard_DS3_v2` | Node type pinned by the cluster policy |
| `num_workers` | number | `0` | Default worker count in the cluster policy |

## Outputs

| Name | Description |
| --- | --- |
| `catalog_name` | Name of the catalog |
| `schema_name` | Name of the schema |
| `cluster_policy_id` | ID of the cluster policy |
| `cluster_policy_name` | Name of the cluster policy |

## Notes

- The policy pins the Spark version and node type, allows 0 to 4 workers, and ends idle clusters after 30 minutes.
- The schema holds the gold tables for analytics. The catalog and schema names are variables, so each environment can keep its own names.
