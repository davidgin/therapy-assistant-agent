# Production Environment Configuration for Therapy Assistant Agent

# Environment
environment = "prod"
aws_region  = "us-west-2"

# Networking
vpc_cidr             = "10.20.0.0/16"
public_subnet_cidrs  = ["10.20.1.0/24", "10.20.2.0/24"]
private_subnet_cidrs = ["10.20.11.0/24", "10.20.12.0/24"]
db_subnet_cidrs     = ["10.20.21.0/24", "10.20.22.0/24"]

# Database (PostgreSQL)
db_instance_class           = "db.t3.medium"
db_engine_version          = "15.4"
db_allocated_storage        = 100
db_backup_retention_period  = 30
db_multi_az                = true

# Compute
instance_type       = "t3.large"
container_cpu       = 1024
container_memory    = 2048
min_capacity        = 2
max_capacity        = 10
desired_capacity    = 3

# Monitoring
enable_monitoring   = true
enable_backup      = true
log_retention_days = 30

# Security
allowed_cidr_blocks = ["10.0.0.0/8"]
enable_https       = true
enable_waf         = true

# Scaling
cpu_target_value      = 60
memory_target_value   = 70
scale_up_cooldown     = 300
scale_down_cooldown   = 600

# Domain (configure with your production domain)
domain_name = "therapy-assistant.example.com"
certificate_arn = "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"