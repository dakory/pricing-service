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
