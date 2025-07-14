# Staging Environment Configuration for Therapy Assistant Agent

# Environment
environment = "staging"
aws_region  = "us-west-2"

# Networking
vpc_cidr             = "10.10.0.0/16"
public_subnet_cidrs  = ["10.10.1.0/24", "10.10.2.0/24"]
private_subnet_cidrs = ["10.10.11.0/24", "10.10.12.0/24"]
db_subnet_cidrs     = ["10.10.21.0/24", "10.10.22.0/24"]

# Database (PostgreSQL)
db_instance_class           = "db.t3.small"
db_engine_version          = "15.4"
db_allocated_storage        = 50
db_backup_retention_period  = 7
db_multi_az                = false

# Compute
instance_type       = "t3.medium"
container_cpu       = 512
container_memory    = 1024
min_capacity        = 1
max_capacity        = 5
desired_capacity    = 2

# Monitoring
enable_monitoring   = true
enable_backup      = true
log_retention_days = 14

# Security
allowed_cidr_blocks = ["10.0.0.0/8"]
enable_https       = true
enable_waf         = true

# Scaling
cpu_target_value      = 70
memory_target_value   = 80
scale_up_cooldown     = 300
scale_down_cooldown   = 300

# Domain (configure with your staging domain)
domain_name = "staging-therapy-assistant.example.com"
certificate_arn = "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"