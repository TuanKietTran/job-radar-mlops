terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_sagemaker_model" "this" {
  name               = "${local.name_prefix}-model"
  execution_role_arn = var.execution_role_arn

  primary_container {
    image          = var.model_image
    model_data_url = var.model_data_url
  }

  tags = var.tags
}

resource "aws_sagemaker_endpoint_configuration" "this" {
  name = "${local.name_prefix}-endpoint-config"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.this.name
    initial_instance_count = var.endpoint_instance_count
    instance_type          = var.instance_type
  }

  tags = var.tags
}

resource "aws_sagemaker_endpoint" "this" {
  name                 = "${local.name_prefix}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.this.name

  tags = var.tags
}
