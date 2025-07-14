# Terraform Infrastructure for Therapy Assistant Agent

This directory contains the Terraform configuration to deploy the Therapy Assistant Agent application on AWS using modern cloud infrastructure practices.

## 🏗️ Architecture Overview

The infrastructure deploys a highly available, scalable, and secure therapy assistant application using:

- **AWS ECS Fargate** for containerized application hosting
- **Application Load Balancer** for traffic distribution
- **Amazon RDS PostgreSQL** for database storage
- **Amazon ECR** for container image registry
- **VPC with public/private subnets** for network isolation
- **CloudWatch** for monitoring and logging
- **Auto Scaling** for dynamic capacity management
- **AWS Secrets Manager** for secure credential storage

## 📁 Project Structure

```
terraform/
├── main.tf                 # Main Terraform configuration
├── variables.tf            # Variable definitions
├── outputs.tf             # Output definitions
├── networking.tf          # Load balancer and networking resources
├── database.tf            # Database module usage
├── compute.tf             # ECS and container resources
├── monitoring.tf          # CloudWatch and monitoring
├── modules/               # Reusable Terraform modules
│   ├── networking/        # VPC, subnets, security groups
│   ├── database/          # RDS PostgreSQL setup
│   ├── compute/           # ECS cluster and services
│   └── monitoring/        # CloudWatch dashboards and alarms
├── environments/          # Environment-specific configurations
│   ├── dev/
│   ├── staging/
│   └── prod/
└── scripts/               # Deployment scripts
    ├── deploy.sh          # Terraform deployment script
    └── build-and-deploy.sh # Complete build and deploy script
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **Docker** installed and running
4. **jq** for JSON processing
5. **OpenAI API Key** for AI services

### Environment Variables

Set the following environment variables before deployment:

```bash
export AWS_DEFAULT_REGION=us-west-2
export OPENAI_API_KEY=your_openai_api_key_here
export TF_VAR_openai_api_key=$OPENAI_API_KEY
```

### Quick Deployment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd therapy-assistant-agent/terraform
   ```

2. **Deploy to development**:
   ```bash
   ./scripts/build-and-deploy.sh dev
   ```

3. **Deploy to staging**:
   ```bash
   ./scripts/build-and-deploy.sh staging
   ```

4. **Deploy to production**:
   ```bash
   ./scripts/build-and-deploy.sh prod
   ```

## 🔧 Configuration

### Environment Configuration

Each environment has its own configuration file in `environments/[env]/terraform.tfvars`:

#### Development (`environments/dev/terraform.tfvars`)
- Minimal resources for development
- Single AZ deployment
- Basic monitoring
- No HTTPS/WAF

#### Staging (`environments/staging/terraform.tfvars`)
- Production-like setup
- Multi-AZ database
- Full monitoring
- HTTPS and WAF enabled

#### Production (`environments/prod/terraform.tfvars`)
- High availability setup
- Multi-AZ database with read replica
- Enhanced monitoring
- Full security features

### Key Configuration Parameters

| Parameter | Description | Dev | Staging | Prod |
|-----------|-------------|-----|---------|------|
| `db_instance_class` | RDS instance size | t3.micro | t3.small | t3.medium |
| `container_cpu` | ECS task CPU | 256 | 512 | 1024 |
| `container_memory` | ECS task memory | 512 | 1024 | 2048 |
| `desired_capacity` | Number of containers | 1 | 2 | 3 |
| `db_multi_az` | Database high availability | false | false | true |
| `enable_https` | HTTPS termination | false | true | true |
| `enable_waf` | Web Application Firewall | false | true | true |

## 📋 Deployment Commands

### Infrastructure Only

```bash
# Plan infrastructure changes
./scripts/deploy.sh dev plan

# Apply infrastructure changes
./scripts/deploy.sh dev apply

# Destroy infrastructure
./scripts/deploy.sh dev destroy

# Show outputs
./scripts/deploy.sh dev output
```

### Complete Deployment

```bash
# Build, push, and deploy everything
./scripts/build-and-deploy.sh dev

# Skip building Docker image
./scripts/build-and-deploy.sh dev --skip-build

# Skip pushing to ECR
./scripts/build-and-deploy.sh dev --skip-push

# Skip infrastructure deployment
./scripts/build-and-deploy.sh dev --skip-deploy

# Force infrastructure redeployment
./scripts/build-and-deploy.sh dev --force-deploy
```

## 🔍 Monitoring and Operations

### CloudWatch Monitoring

The infrastructure includes comprehensive monitoring:

- **Application Metrics**: CPU, memory, request count
- **Database Metrics**: CPU, connections, storage
- **Load Balancer Metrics**: Response time, error rates
- **Custom Dashboards**: Environment-specific views
- **Automated Alarms**: SNS notifications for issues

### Accessing Logs

```bash
# Get log group name
terraform output cloudwatch_log_group_name

# View logs using AWS CLI
aws logs tail /ecs/therapy-assistant-agent-dev-app --follow
```

### Health Checks

The application includes health check endpoints:

- **Health Check**: `/health` - Basic application health
- **Load Balancer**: Automatic health checks for ECS tasks

## 🔐 Security Features

### Network Security

- **VPC Isolation**: Private subnets for application and database
- **Security Groups**: Restrictive ingress/egress rules
- **NAT Gateways**: Secure internet access for private resources
- **VPC Endpoints**: Private connectivity to AWS services

### Data Protection

- **Encryption at Rest**: RDS and ECS volumes encrypted
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Secrets Management**: AWS Secrets Manager for credentials
- **KMS Keys**: Customer-managed encryption keys

### Access Control

- **IAM Roles**: Least privilege access for ECS tasks
- **WAF Protection**: Web Application Firewall (staging/prod)
- **Rate Limiting**: Application-level rate limiting
- **CORS**: Proper CORS configuration

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      - name: Deploy to staging
        run: |
          cd terraform
          ./scripts/build-and-deploy.sh staging
```

### Manual Deployment Workflow

1. **Development**: 
   - Local development and testing
   - Deploy to dev environment for integration testing

2. **Staging**:
   - Deploy to staging for pre-production testing
   - Run automated tests against staging

3. **Production**:
   - Deploy to production after staging validation
   - Monitor deployment metrics

## 🛠️ Troubleshooting

### Common Issues

#### ECS Service Not Starting

```bash
# Check ECS service status
aws ecs describe-services --cluster therapy-assistant-agent-dev-cluster --services therapy-assistant-agent-dev-app

# Check ECS task logs
aws logs tail /ecs/therapy-assistant-agent-dev-app --follow
```

#### Database Connection Issues

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier therapy-assistant-agent-dev-db

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
```

#### Load Balancer Issues

```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# Check load balancer status
aws elbv2 describe-load-balancers --names therapy-assistant-agent-dev-alb
```

### Debug Commands

```bash
# Get all outputs
terraform output

# Refresh state
terraform refresh -var-file=environments/dev/terraform.tfvars

# Import existing resources
terraform import aws_lb.main arn:aws:elasticloadbalancing:...
```

## 💰 Cost Optimization

### Development Environment

- Uses t3.micro instances
- Single AZ deployment
- Minimal log retention
- Basic monitoring

**Estimated Monthly Cost**: $50-100

### Production Environment

- Uses t3.medium instances
- Multi-AZ deployment
- Enhanced monitoring
- Full security features

**Estimated Monthly Cost**: $200-400

### Cost Optimization Tips

1. **Right-size resources** based on actual usage
2. **Use Spot instances** for non-critical workloads
3. **Enable auto-scaling** to handle variable load
4. **Set up billing alerts** for cost monitoring
5. **Review unused resources** regularly

## 🔧 Customization

### Adding New Environments

1. Create new tfvars file: `environments/[env]/terraform.tfvars`
2. Update deployment scripts to recognize new environment
3. Configure environment-specific settings

### Modifying Infrastructure

1. Update module configurations in `modules/`
2. Modify main configuration files
3. Test changes in development first
4. Use `terraform plan` to preview changes

### Adding New Services

1. Create new module in `modules/`
2. Add module usage in main configuration
3. Update outputs and variables
4. Document new service configuration

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [AWS RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test in development
4. Submit a pull request with detailed description
5. Ensure all security best practices are followed

## 📞 Support

For deployment issues or questions:

1. Check this documentation first
2. Review CloudWatch logs and metrics
3. Check AWS service health status
4. Contact the development team with specific error messages

---

**Note**: This infrastructure is designed for the Therapy Assistant Agent application. Modify configurations according to your specific requirements and security policies.