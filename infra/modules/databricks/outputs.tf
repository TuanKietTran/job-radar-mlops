output "catalog_name" {
  description = "Name of the catalog."
  value       = databricks_catalog.this.name
}

output "schema_name" {
  description = "Name of the schema."
  value       = databricks_schema.this.name
}

output "cluster_policy_id" {
  description = "ID of the cluster policy."
  value       = databricks_cluster_policy.this.id
}

output "cluster_policy_name" {
  description = "Name of the cluster policy."
  value       = databricks_cluster_policy.this.name
}
