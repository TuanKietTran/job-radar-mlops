terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region
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

variable "aws_region" {
  description = "AWS region for the stack."
  type        = string
  default     = "ap-southeast-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "Region must look like ap-southeast-1."
  }
}

variable "sagemaker_instance_type" {
  description = "SageMaker instance type for the endpoint."
  type        = string
  default     = "ml.t3.medium"

  validation {
    condition     = can(regex("^ml\\.[a-z0-9]+\\.[a-z0-9]+$", var.sagemaker_instance_type))
    error_message = "Instance type must look like ml.t3.medium."
  }
}

variable "model_image" {
  description = "Container image for the SageMaker model. Replace with the registry image built by the training run."
  type        = string
  default     = "job-radar/train:0.1.0"
}

variable "model_data_url" {
  description = "S3 URL of the model artefacts. Null when the image holds the model."
  type        = string
  default     = null
}

module "lakehouse" {
  source        = "../modules/aws-s3"
  bucket_prefix = var.project
  environment   = var.environment
}

module "images" {
  source       = "../modules/aws-ecr"
  project      = var.project
  environment  = var.environment
  repositories = ["api", "train"]
}

module "roles" {
  source               = "../modules/aws-iam"
  project              = var.project
  environment          = var.environment
  lakehouse_bucket_arn = module.lakehouse.bucket_arn
  api_repository_arn   = module.images.repository_arns["api"]
  train_repository_arn = module.images.repository_arns["train"]
  endpoint_name        = "${var.project}-${var.environment}-endpoint"
}

module "serving" {
  source             = "../modules/aws-sagemaker"
  project            = var.project
  environment        = var.environment
  model_image        = var.model_image
  model_data_url     = var.model_data_url
  instance_type      = var.sagemaker_instance_type
  execution_role_arn = module.roles.serve_role_arn
}

output "lakehouse_bucket" {
  description = "Name of the lakehouse bucket."
  value       = module.lakehouse.bucket_id
}

output "api_repository_url" {
  description = "URL of the api image repository."
  value       = module.images.repository_urls["api"]
}

output "train_repository_url" {
  description = "URL of the train image repository."
  value       = module.images.repository_urls["train"]
}

output "sagemaker_endpoint_name" {
  description = "Name of the SageMaker endpoint."
  value       = module.serving.endpoint_name
}
