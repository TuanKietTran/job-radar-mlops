terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "azurerm_machine_learning_workspace" "this" {
  name                    = "${local.name_prefix}-ml"
  location                = var.location
  resource_group_name     = var.resource_group_name
  application_insights_id = var.application_insights_id
  key_vault_id            = var.key_vault_id
  storage_account_id      = var.storage_account_id

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_machine_learning_compute_cluster" "this" {
  name                          = "train"
  location                      = var.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.this.id
  vm_priority                   = "Dedicated"
  vm_size                       = var.compute_vm_size

  scale_settings {
    min_node_count                       = var.compute_min_nodes
    max_node_count                       = var.compute_max_nodes
    scale_down_nodes_after_idle_duration = "PT120S"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azapi_resource" "online_endpoint" {
  type      = "Microsoft.MachineLearningServices/workspaces/onlineEndpoints@2024-10-01"
  name      = "${local.name_prefix}-endpoint"
  parent_id = azurerm_machine_learning_workspace.this.id
  location  = var.location

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      authMode = "AMLToken"
    }
  }

  tags = var.tags
}
