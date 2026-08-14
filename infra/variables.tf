variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "app_name" {
  description = "Project name"
  type        = string
  default     = "pricing-service"
}

variable "domain" {
  description = "Public dashboard domain"
  type        = string
  default     = "pricing.nicer.homes"
}

variable "app_volume_size" {
  description = "Persistent application EBS volume size in GiB"
  type        = number
  default     = 20
}

variable "competitor_lambda_image_uri" {
  description = "Immutable ECR image URI for the competitor Lambda; leave empty during the initial repository-only apply"
  type        = string
  default     = ""
}

variable "competitor_callback_url" {
  description = "Authenticated backend endpoint receiving competitor scrape results"
  type        = string
  default     = ""
}

variable "competitor_lambda_timeout" {
  description = "Maximum collector execution time in seconds"
  type        = number
  default     = 60
}

variable "competitor_lambda_reserved_concurrency" {
  description = "Reserved Lambda concurrency; use -1 when the account quota cannot reserve one execution"
  type        = number
  default     = -1

  validation {
    condition     = var.competitor_lambda_reserved_concurrency == -1 || var.competitor_lambda_reserved_concurrency == 1
    error_message = "Reserved concurrency must be -1 (unreserved) or 1 (serialized)."
  }
}
