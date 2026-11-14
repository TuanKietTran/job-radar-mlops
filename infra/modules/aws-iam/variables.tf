variable "project" {
  description = "Project name used as a prefix for role names."
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

variable "lakehouse_bucket_arn" {
  description = "ARN of the lakehouse bucket."
  type        = string
}

variable "api_repository_arn" {
  description = "ARN of the api image repository."
  type        = string
}

variable "train_repository_arn" {
  description = "ARN of the train image repository."
  type        = string
}

variable "endpoint_name" {
  description = "Name of the SageMaker endpoint the serve role may invoke. Defaults to <project>-<environment>-endpoint."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags applied to the roles and policies."
  type        = map(string)
  default     = {}
}
