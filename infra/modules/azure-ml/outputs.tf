output "workspace_id" {
  description = "ID of the machine learning workspace."
  value       = azurerm_machine_learning_workspace.this.id
}

output "workspace_name" {
  description = "Name of the machine learning workspace."
  value       = azurerm_machine_learning_workspace.this.name
}

output "compute_cluster_name" {
  description = "Name of the training compute cluster."
  value       = azurerm_machine_learning_compute_cluster.this.name
}

output "endpoint_name" {
  description = "Name of the online endpoint."
  value       = azapi_resource.online_endpoint.name
}
