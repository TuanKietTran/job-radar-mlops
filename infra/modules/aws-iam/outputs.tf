output "train_role_arn" {
  description = "ARN of the train role."
  value       = aws_iam_role.train.arn
}

output "serve_role_arn" {
  description = "ARN of the serve role."
  value       = aws_iam_role.serve.arn
}

output "ingest_role_arn" {
  description = "ARN of the ingest role."
  value       = aws_iam_role.ingest.arn
}

output "train_role_name" {
  description = "Name of the train role."
  value       = aws_iam_role.train.name
}

output "serve_role_name" {
  description = "Name of the serve role."
  value       = aws_iam_role.serve.name
}

output "ingest_role_name" {
  description = "Name of the ingest role."
  value       = aws_iam_role.ingest.name
}
