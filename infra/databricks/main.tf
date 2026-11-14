terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "databricks" {}

variable "project" {
  description = "Project name used as a prefix for the cluster policy name."
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

variable "catalog_name" {
  description = "Name of the catalog."
  type        = string
  default     = "job_radar"

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{2,30}$", var.catalog_name))
    error_message = "Catalog name must be 3 to 31 lowercase letters, digits or underscores, starting with a letter."
  }
}

variable "schema_name" {
  description = "Name of the schema."
  type        = string
  default     = "gold"

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{2,30}$", var.schema_name))
    error_message = "Schema name must be 3 to 31 lowercase letters, digits or underscores, starting with a letter."
  }
}

module "lakehouse" {
  source       = "../modules/databricks"
  project      = var.project
  environment  = var.environment
  catalog_name = var.catalog_name
  schema_name  = var.schema_name
}

output "catalog_name" {
  description = "Name of the catalog."
  value       = module.lakehouse.catalog_name
}

output "schema_name" {
  description = "Name of the schema."
  value       = module.lakehouse.schema_name
}

output "cluster_policy_name" {
  description = "Name of the cluster policy."
  value       = module.lakehouse.cluster_policy_name
}
