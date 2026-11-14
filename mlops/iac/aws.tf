terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5"
}

# Variables only. No credentials, account numbers, or real bucket names.
# Set values with an uncommitted tfvars file, or with a variable flag.
variable "project" { type = string }
variable "environment" { type = string }
variable "region" { type = string }
variable "lake_bucket_name" { type = string }
variable "training_image" { type = string }
variable "serving_instance_type" { type = string }
variable "canary_percent" {
  type    = number
  default = 0
}
variable "sagemaker_role_arn" { type = string }

resource "aws_s3_bucket" "lake" {
  bucket = var.lake_bucket_name
  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_sagemaker_model" "salary" {
  name               = var.project
  execution_role_arn = var.sagemaker_role_arn
  primary_container {
    image = var.training_image
  }
}

# Serving endpoint, monitoring, networking, and permissions are set by
# the team that owns the account, and recorded with the run evidence.
