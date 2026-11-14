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

variable "spark_version" {
  description = "Spark version pinned by the cluster policy."
  type        = string
  default     = "15.4.x-scala2.12"
}

variable "node_type_id" {
  description = "Node type pinned by the cluster policy."
  type        = string
  default     = "Standard_DS3_v2"
}

variable "num_workers" {
  description = "Default worker count in the cluster policy."
  type        = number
  default     = 0

  validation {
    condition     = var.num_workers >= 0 && var.num_workers <= 4
    error_message = "Worker count must be between 0 and 4."
  }
}
