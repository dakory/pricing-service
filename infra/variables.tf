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

variable "image_tag" {
  description = "Docker image tag to run"
  type        = string
  default     = "latest"
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
