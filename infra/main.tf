data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

data "aws_caller_identity" "current" {}

resource "aws_security_group" "app" {
  name        = "${var.app_name}-sg"
  description = "Security group for ${var.app_name}"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-sg"
  }
}

resource "aws_iam_role" "ec2_role" {
  name = "${var.app_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_kms_key" "backups" {
  description             = "Encrypt ${var.app_name} database backups"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_s3_bucket" "backups" {
  bucket_prefix = "${var.app_name}-backups-"
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket                  = aws_s3_bucket.backups.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id
  rule {
    blocked_encryption_types = ["SSE-C"]
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.backups.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id
  rule {
    id     = "expire-old-backups"
    status = "Enabled"
    expiration {
      days = 90
    }
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_ssm_parameter" "hostex_token" {
  name        = "/${var.app_name}/hostex-access-token"
  description = "Hostex API token; set the value after provisioning"
  type        = "SecureString"
  key_id      = aws_kms_key.backups.arn
  value       = "REPLACE_ME"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "app_secrets" {
  name        = "/${var.app_name}/app-secrets"
  description = "JSON containing POSTGRES_PASSWORD, ADMIN_PASSWORD and SESSION_SECRET"
  type        = "SecureString"
  key_id      = aws_kms_key.backups.arn
  value       = jsonencode({ bootstrap = "REPLACE_ME" })

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "competitor_callback_token" {
  name        = "/${var.app_name}/competitor-callback-token"
  description = "Bearer token shared by the competitor Lambda and backend"
  type        = "SecureString"
  tier        = "Standard"
  key_id      = aws_kms_key.backups.arn
  value       = "REPLACE_ME"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "competitor_airbnb_config" {
  name        = "/${var.app_name}/competitor-airbnb-config"
  description = "JSON runtime config for the Airbnb frontend API: api_key, client_version, calendar_sha, checkout_sha, optional paths and collector_paused; empty object uses the fixture defaults baked into the Lambda image"
  type        = "SecureString"
  tier        = "Standard"
  key_id      = aws_kms_key.backups.arn
  value       = jsonencode({})

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_iam_role_policy" "application_data" {
  name = "${var.app_name}-application-data"
  role = aws_iam_role.ec2_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = [aws_ssm_parameter.hostex_token.arn, aws_ssm_parameter.app_secrets.arn, aws_ssm_parameter.competitor_callback_token.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.backups.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.backups.arn, "${aws_s3_bucket.backups.arn}/*"]
      }
    ]
  })
}

resource "aws_ebs_volume" "app_data" {
  availability_zone = aws_instance.app.availability_zone
  size              = var.app_volume_size
  type              = "gp3"
  encrypted         = true
  tags = {
    Name = "${var.app_name}-data"
  }
}

resource "aws_volume_attachment" "app_data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.app_data.id
  instance_id = aws_instance.app.id
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.app_name}-instance-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_ecr_repository" "app" {
  name                 = var.app_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = var.app_name
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the six newest API and dashboard releases"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 6
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_repository" "competitor_lambda" {
  name                 = "${var.app_name}-competitor-lambda"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.app_name}-competitor-lambda"
  }
}

resource "aws_ecr_lifecycle_policy" "competitor_lambda" {
  repository = aws_ecr_repository.competitor_lambda.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the three newest Lambda images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 3
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_iam_role" "competitor_lambda" {
  name = "${var.app_name}-competitor-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_cloudwatch_log_group" "competitor_lambda" {
  name              = "/aws/lambda/${var.app_name}-competitor-collector"
  retention_in_days = 7
}

resource "aws_iam_role_policy" "competitor_lambda" {
  name = "${var.app_name}-competitor-lambda-policy"
  role = aws_iam_role.competitor_lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.competitor_lambda.arn}:*"
      },
      {
        Effect = "Allow"
        Action = ["ssm:GetParameter"]
        Resource = [
          aws_ssm_parameter.competitor_callback_token.arn,
          aws_ssm_parameter.competitor_airbnb_config.arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = aws_kms_key.backups.arn
      }
    ]
  })
}

resource "aws_lambda_function" "competitor_collector" {
  count = var.competitor_lambda_image_uri == "" ? 0 : 1

  function_name = "${var.app_name}-competitor-collector"
  role          = aws_iam_role.competitor_lambda.arn
  package_type  = "Image"
  image_uri     = var.competitor_lambda_image_uri
  architectures = ["x86_64"]
  memory_size   = 256
  timeout       = var.competitor_lambda_timeout

  # New AWS accounts can have a concurrency quota of only 10 and AWS requires
  # all 10 to remain unreserved. Use -1 until the account quota is increased;
  # backend run locks still prevent overlapping work for a listing/range.
  reserved_concurrent_executions = var.competitor_lambda_reserved_concurrency

  environment {
    variables = {
      BACKEND_CALLBACK_URL             = var.competitor_callback_url != "" ? var.competitor_callback_url : "https://${var.domain}/api/internal/competitor-observations"
      BACKEND_CALLBACK_TOKEN_PARAMETER = aws_ssm_parameter.competitor_callback_token.name
      AIRBNB_FRONTEND_CONFIG_PARAMETER = aws_ssm_parameter.competitor_airbnb_config.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.competitor_lambda,
    aws_iam_role_policy.competitor_lambda,
  ]
}

resource "aws_iam_role_policy" "invoke_competitor_lambda" {
  count = var.competitor_lambda_image_uri == "" ? 0 : 1

  name = "${var.app_name}-invoke-competitor-lambda"
  role = aws_iam_role.ec2_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = aws_lambda_function.competitor_collector[0].arn
    }]
  })
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    aws_region     = var.aws_region
    repository_url = aws_ecr_repository.app.repository_url
    app_name       = var.app_name
    domain         = var.domain
    backup_bucket  = aws_s3_bucket.backups.id
    backup_kms_key = aws_kms_key.backups.arn
  })

  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name = var.app_name
  }
}

resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id
  tags = {
    Name = "${var.app_name}-eip"
  }
}
