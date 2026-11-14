variable "project" {
  description = "Project name used as a prefix for repository names."
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

variable "repositories" {
  description = "Repository names, one per image."
  type        = list(string)
  default     = ["api", "train"]

  validation {
    condition     = length(var.repositories) > 0 && alltrue([for r in var.repositories : can(regex("^[a-z][a-z0-9-]{1,30}$", r))])
    error_message = "Each repository name must be 2 to 31 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "scan_on_push" {
  description = "Scan each image for vulnerabilities on push."
  type        = bool
  default     = true
}

variable "force_delete" {
  description = "Allow Terraform to delete a repository holding images."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags applied to the repositories."
  type        = map(string)
  default     = {}
}
