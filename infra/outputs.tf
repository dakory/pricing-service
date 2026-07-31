output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "instance_id" {
  value = aws_instance.app.id
}

output "public_ip" {
  value = aws_instance.app.public_ip
}

output "ssm_hint" {
  value = "Connect via AWS Console or: aws ssm start-session --target ${aws_instance.app.id}"
}
output "elastic_ip" {
  description = "Create an A record for the configured domain pointing here"
  value       = aws_eip.app.public_ip
}

output "backup_bucket" {
  value = aws_s3_bucket.backups.id
}

output "hostex_parameter_name" {
  value = aws_ssm_parameter.hostex_token.name
}

output "competitor_lambda_repository_url" {
  value = aws_ecr_repository.competitor_lambda.repository_url
}

output "competitor_lambda_name" {
  value = try(aws_lambda_function.competitor_collector[0].function_name, null)
}

output "competitor_lambda_arn" {
  value = try(aws_lambda_function.competitor_collector[0].arn, null)
}

output "competitor_callback_parameter_name" {
  value = aws_ssm_parameter.competitor_callback_token.name
}
