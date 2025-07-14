# Therapy Assistant Agent - Terraform Infrastructure
# Main configuration for deploying the therapy assistant platform

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "therapy-assistant-agent"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "therapy-assistant-team"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "therapy-assistant-team"
  }
  
  # Database configuration
  db_name = "${replace(var.project_name, "-", "_")}_${var.environment}"
  
  # Container configuration
  container_port = 8000
  health_check_path = "/health"
  
  # Security
  allowed_cidr_blocks = var.environment == "prod" ? ["10.0.0.0/8"] : ["0.0.0.0/0"]
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Generate JWT secret key
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Generate application secret key
resource "random_password" "app_secret" {
  length  = 64
  special = true
}