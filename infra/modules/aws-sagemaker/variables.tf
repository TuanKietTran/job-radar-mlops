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

variable "model_image" {
  description = "Container image for the model."
  type        = string
}

variable "model_data_url" {
  description = "S3 URL of the model artefacts. Null when the image holds the model."
  type        = string
  default     = null
}

variable "instance_type" {
  description = "SageMaker instance type for the endpoint."
  type        = string
  default     = "ml.t3.medium"

  validation {
    condition     = can(regex("^ml\\.[a-z0-9]+\\.[a-z0-9]+$", var.instance_type))
    error_message = "Instance type must look like ml.t3.medium."
  }
}

variable "endpoint_instance_count" {
  description = "Number of endpoint instances."
  type        = number
  default     = 1

  validation {
    condition     = var.endpoint_instance_count >= 1 && var.endpoint_instance_count <= 3
    error_message = "Endpoint instance count must be between 1 and 3."
  }
}

variable "execution_role_arn" {
  description = "ARN of the role SageMaker assumes to run the model."
  type        = string
}

variable "tags" {
  description = "Tags applied to the SageMaker resources."
  type        = map(string)
  default     = {}
}
