# Outputs for Therapy Assistant Agent Infrastructure

# Networking Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

# Load Balancer Outputs
output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

# Database Outputs
output "database_endpoint" {
  description = "Database endpoint"
  value       = module.database.db_instance_endpoint
}

output "database_port" {
  description = "Database port"
  value       = module.database.db_instance_port
}

output "database_name" {
  description = "Database name"
  value       = module.database.db_instance_name
}

output "database_secrets_manager_secret_arn" {
  description = "ARN of the database credentials in Secrets Manager"
  value       = module.database.db_secrets_manager_secret_arn
}

# Compute Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.compute.ecs_cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.compute.ecs_service_name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.compute.ecr_repository_url
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.compute.cloudwatch_log_group_name
}

# Application URLs
output "application_url" {
  description = "URL to access the application"
  value       = var.domain_name != "" ? (var.enable_https ? "https://${var.domain_name}" : "http://${var.domain_name}") : (var.enable_https ? "https://${aws_lb.main.dns_name}" : "http://${aws_lb.main.dns_name}")
}

output "health_check_url" {
  description = "URL for health check"
  value       = "${var.enable_https ? "https" : "http"}://${var.domain_name != "" ? var.domain_name : aws_lb.main.dns_name}${local.health_check_path}"
}

# Monitoring Outputs
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = var.enable_monitoring ? aws_sns_topic.alerts[0].arn : ""
}

output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = var.enable_monitoring ? "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${local.name_prefix}-dashboard" : ""
}

# Security Outputs
output "security_group_ids" {
  description = "Security group IDs"
  value = {
    alb = module.networking.alb_security_group_id
    ecs = module.networking.ecs_security_group_id
    rds = module.networking.rds_security_group_id
  }
}

# Environment Configuration
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# Container Registry
output "container_registry_commands" {
  description = "Commands to push container to ECR"
  value = [
    "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.compute.ecr_repository_url}",
    "docker build -t ${local.name_prefix}-app .",
    "docker tag ${local.name_prefix}-app:latest ${module.compute.ecr_repository_url}:latest",
    "docker push ${module.compute.ecr_repository_url}:latest"
  ]
}

# Database Connection String
output "database_connection_info" {
  description = "Information needed to connect to the database"
  value = {
    host     = module.database.db_instance_endpoint
    port     = module.database.db_instance_port
    database = module.database.db_instance_name
    username = module.database.db_instance_username
    # Note: Password is stored in Secrets Manager
    secrets_manager_secret_arn = module.database.db_secrets_manager_secret_arn
  }
  sensitive = true
}

# Terraform State Information
output "terraform_state_info" {
  description = "Information about the Terraform state"
  value = {
    workspace = terraform.workspace
    version   = "~> 1.0"
  }
}

# Resource ARNs for monitoring and management
output "resource_arns" {
  description = "ARNs of key resources"
  value = {
    load_balancer = aws_lb.main.arn
    ecs_cluster   = module.compute.ecs_cluster_name
    ecs_service   = "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:service/${module.compute.ecs_cluster_name}/${module.compute.ecs_service_name}"
    database      = module.database.db_instance_arn
    ecr_repository = module.compute.ecr_repository_arn
  }
}