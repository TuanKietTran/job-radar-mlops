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
  description = "Azure region for the workspace."
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

variable "compute_min_nodes" {
  description = "Minimum nodes for the training compute cluster."
  type        = number
  default     = 0

  validation {
    condition     = var.compute_min_nodes >= 0 && var.compute_min_nodes <= var.compute_max_nodes
    error_message = "Minimum nodes must be between 0 and the maximum nodes."
  }
}

variable "compute_max_nodes" {
  description = "Maximum nodes for the training compute cluster."
  type        = number
  default     = 2

  validation {
    condition     = var.compute_max_nodes >= 1 && var.compute_max_nodes <= 10
    error_message = "Maximum nodes must be between 1 and 10."
  }
}

variable "tags" {
  description = "Tags applied to the workspace resources."
  type        = map(string)
  default     = {}
}
