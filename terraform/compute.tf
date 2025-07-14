# Compute Resources for Therapy Assistant Agent

# Use compute module
module "compute" {
  source = "./modules/compute"

  name_prefix                    = local.name_prefix
  environment                   = var.environment
  aws_region                    = var.aws_region
  private_subnet_ids            = module.networking.private_subnet_ids
  ecs_security_group_id         = module.networking.ecs_security_group_id
  alb_target_group_arn          = aws_lb_target_group.app.arn
  container_port                = local.container_port
  container_cpu                 = var.container_cpu
  container_memory              = var.container_memory
  min_capacity                  = var.min_capacity
  max_capacity                  = var.max_capacity
  desired_capacity              = var.desired_capacity
  cpu_target_value              = var.cpu_target_value
  memory_target_value           = var.memory_target_value
  scale_up_cooldown             = var.scale_up_cooldown
  scale_down_cooldown           = var.scale_down_cooldown
  health_check_path             = local.health_check_path
  log_retention_days            = var.log_retention_days
  database_url                  = module.database.database_url
  app_secret_key                = random_password.app_secret.result
  jwt_secret_key                = random_password.jwt_secret.result
  openai_api_key                = var.openai_api_key
  db_secrets_manager_secret_arn = module.database.db_secrets_manager_secret_arn
  enable_monitoring             = var.enable_monitoring
  sns_topic_arn                 = var.enable_monitoring ? aws_sns_topic.alerts[0].arn : ""
  common_tags                   = local.common_tags

  depends_on = [
    module.networking,
    module.database,
    aws_lb_target_group.app
  ]
}