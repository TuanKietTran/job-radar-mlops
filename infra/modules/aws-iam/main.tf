terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  endpoint_name = var.endpoint_name != "" ? var.endpoint_name : "${var.project}-${var.environment}-endpoint"
  endpoint_arn  = "arn:aws:sagemaker:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:endpoint/${local.endpoint_name}"
}

# Train role: reads and writes the lakehouse, pulls the train image.
resource "aws_iam_role" "train" {
  name = "${var.project}-${var.environment}-train"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "train" {
  name = "${var.project}-${var.environment}-train"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          var.lakehouse_bucket_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${var.lakehouse_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = [
          var.train_repository_arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "train" {
  role       = aws_iam_role.train.name
  policy_arn = aws_iam_policy.train.arn
}

# Serve role: reads the lakehouse, pulls the api image, invokes the endpoint.
resource "aws_iam_role" "serve" {
  name = "${var.project}-${var.environment}-serve"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "serve" {
  name = "${var.project}-${var.environment}-serve"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${var.lakehouse_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = [
          var.api_repository_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = [
          local.endpoint_arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "serve" {
  role       = aws_iam_role.serve.name
  policy_arn = aws_iam_policy.serve.arn
}

# Ingest role: writes raw listings to the lakehouse and nothing else.
resource "aws_iam_role" "ingest" {
  name = "${var.project}-${var.environment}-ingest"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "ingest" {
  name = "${var.project}-${var.environment}-ingest"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          var.lakehouse_bucket_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${var.lakehouse_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingest" {
  role       = aws_iam_role.ingest.name
  policy_arn = aws_iam_policy.ingest.arn
}
