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

variable "container_port" {
  description = "Port your app listens on inside the container"
  type        = number
  default     = 8000
}

variable "host_port" {
  description = "Port exposed on the EC2 host"
  type        = number
  default     = 80
}

variable "image_tag" {
  description = "Docker image tag to run"
  type        = string
  default     = "latest"
}
