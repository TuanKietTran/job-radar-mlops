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

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

variable "project" {
  description = "Project name used as a prefix for resource names."
  type        = string
  default     = "job-radar"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project))
    error_message = "Project must be 3 to 31 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging or prod."
  }
}

variable "location" {
  description = "Azure region for the stack."
  type        = string
  default     = "southeastasia"
}

variable "resource_group_name" {
  description = "Name of the resource group that holds the workspace."
  type        = string
}

variable "storage_account_id" {
  description = "ID of the storage account for the workspace."
  type        = string
}

variable "key_vault_id" {
  description = "ID of the key vault for the workspace."
  type        = string
}

variable "application_insights_id" {
  description = "ID of the Application Insights resource for the workspace."
  type        = string
}

variable "compute_vm_size" {
  description = "VM size for the training compute cluster."
  type        = string
  default     = "Standard_DS3_v2"
}

module "ml" {
  source                  = "../modules/azure-ml"
  project                 = var.project
  environment             = var.environment
  location                = var.location
  resource_group_name     = var.resource_group_name
  storage_account_id      = var.storage_account_id
  key_vault_id            = var.key_vault_id
  application_insights_id = var.application_insights_id
  compute_vm_size         = var.compute_vm_size
}

output "workspace_id" {
  description = "ID of the machine learning workspace."
  value       = module.ml.workspace_id
}

output "workspace_name" {
  description = "Name of the machine learning workspace."
  value       = module.ml.workspace_name
}

output "endpoint_name" {
  description = "Name of the online endpoint."
  value       = module.ml.endpoint_name
}
