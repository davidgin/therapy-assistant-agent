# Database Resources for Therapy Assistant Agent

# Use database module
module "database" {
  source = "./modules/database"

  name_prefix              = local.name_prefix
  environment             = var.environment
  database_subnet_ids     = module.networking.database_subnet_ids
  rds_security_group_id   = module.networking.rds_security_group_id
  db_name                 = local.db_name
  db_password             = random_password.db_password.result
  db_instance_class       = var.db_instance_class
  db_engine_version       = var.db_engine_version
  db_allocated_storage    = var.db_allocated_storage
  db_backup_retention_period = var.db_backup_retention_period
  db_multi_az             = var.db_multi_az
  enable_monitoring       = var.enable_monitoring
  create_read_replica     = var.environment == "prod" ? true : false
  sns_topic_arn          = var.enable_monitoring ? aws_sns_topic.alerts[0].arn : ""
  common_tags            = local.common_tags
}