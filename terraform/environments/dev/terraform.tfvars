# Development Environment Configuration for Therapy Assistant Agent

# Environment
environment = "dev"
aws_region  = "us-west-2"

# Networking
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
db_subnet_cidrs     = ["10.0.21.0/24", "10.0.22.0/24"]

# Database (PostgreSQL)
db_instance_class           = "db.t3.micro"
db_engine_version          = "15.4"
db_allocated_storage        = 20
db_backup_retention_period  = 1
db_multi_az                = false

# Compute
instance_type       = "t3.small"
container_cpu       = 256
container_memory    = 512
min_capacity        = 1
max_capacity        = 3
desired_capacity    = 1

# Monitoring
enable_monitoring   = true
enable_backup      = false
log_retention_days = 7

# Security
allowed_cidr_blocks = ["0.0.0.0/0"]
enable_https       = false
enable_waf         = false

# Scaling
cpu_target_value      = 70
memory_target_value   = 80
scale_up_cooldown     = 300
scale_down_cooldown   = 300

# Domain (optional for dev)
domain_name = ""
certificate_arn = ""