#!/bin/bash

# Complete Build and Deploy Script for Therapy Assistant Agent
# This script builds the Docker image and deploys it to AWS

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    echo "Usage: $0 [environment] [options]"
    echo ""
    echo "Environments:"
    echo "  dev       - Development environment"
    echo "  staging   - Staging environment"
    echo "  prod      - Production environment"
    echo ""
    echo "Options:"
    echo "  --skip-build      Skip Docker image build"
    echo "  --skip-push       Skip Docker image push"
    echo "  --skip-deploy     Skip infrastructure deployment"
    echo "  --force-deploy    Force deployment even if infrastructure exists"
    echo ""
    echo "Examples:"
    echo "  $0 dev"
    echo "  $0 staging --skip-build"
    echo "  $0 prod --force-deploy"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install jq first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

get_ecr_repository_url() {
    local env=$1
    
    cd "$TERRAFORM_DIR"
    
    # Check if infrastructure exists
    if ! terraform workspace list | grep -q "$env"; then
        log_error "Terraform workspace '$env' does not exist. Please deploy infrastructure first."
        exit 1
    fi
    
    terraform workspace select "$env"
    
    # Get ECR repository URL from Terraform output
    local ecr_url=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
    
    if [[ -z "$ecr_url" ]]; then
        log_error "ECR repository URL not found. Please deploy infrastructure first."
        exit 1
    fi
    
    echo "$ecr_url"
}

build_docker_image() {
    local env=$1
    local image_name="therapy-assistant-agent-$env"
    
    log_info "Building Docker image for environment: $env"
    
    cd "$PROJECT_ROOT"
    
    # Build the Docker image
    docker build \
        -t "$image_name:latest" \
        -f backend/Dockerfile \
        .
    
    log_success "Docker image built: $image_name:latest"
}

push_docker_image() {
    local env=$1
    local ecr_url=$2
    local image_name="therapy-assistant-agent-$env"
    
    log_info "Pushing Docker image to ECR: $ecr_url"
    
    # Get AWS account ID and region
    local aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    local aws_region=$(aws configure get region || echo "us-west-2")
    
    # Login to ECR
    aws ecr get-login-password --region "$aws_region" | docker login --username AWS --password-stdin "$aws_account_id.dkr.ecr.$aws_region.amazonaws.com"
    
    # Tag the image
    docker tag "$image_name:latest" "$ecr_url:latest"
    
    # Push the image
    docker push "$ecr_url:latest"
    
    log_success "Docker image pushed to ECR: $ecr_url:latest"
}

deploy_infrastructure() {
    local env=$1
    local force_deploy=$2
    
    log_info "Deploying infrastructure for environment: $env"
    
    cd "$TERRAFORM_DIR"
    
    # Check if infrastructure already exists
    if terraform workspace list | grep -q "$env" && [[ "$force_deploy" != "true" ]]; then
        log_info "Infrastructure already exists for environment: $env"
        log_info "Updating existing infrastructure..."
        
        # Run terraform plan and apply
        ./scripts/deploy.sh "$env" plan
        ./scripts/deploy.sh "$env" apply
    else
        log_info "Creating new infrastructure for environment: $env"
        
        # Deploy infrastructure
        ./scripts/deploy.sh "$env" apply
    fi
    
    log_success "Infrastructure deployment completed for environment: $env"
}

update_ecs_service() {
    local env=$1
    
    log_info "Updating ECS service for environment: $env"
    
    cd "$TERRAFORM_DIR"
    
    # Get ECS cluster and service names
    local cluster_name=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")
    local service_name=$(terraform output -raw ecs_service_name 2>/dev/null || echo "")
    
    if [[ -z "$cluster_name" || -z "$service_name" ]]; then
        log_error "ECS cluster or service name not found. Please check infrastructure deployment."
        exit 1
    fi
    
    # Force new deployment to pick up the new image
    aws ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --force-new-deployment \
        --query 'service.serviceName' \
        --output text
    
    log_success "ECS service updated: $service_name"
    
    # Wait for deployment to complete
    log_info "Waiting for deployment to complete..."
    aws ecs wait services-stable \
        --cluster "$cluster_name" \
        --services "$service_name"
    
    log_success "Deployment completed successfully!"
}

show_deployment_info() {
    local env=$1
    
    cd "$TERRAFORM_DIR"
    
    log_info "Deployment Information for environment: $env"
    echo ""
    
    # Get application URL
    local app_url=$(terraform output -raw application_url 2>/dev/null || echo "")
    if [[ -n "$app_url" ]]; then
        echo "Application URL: $app_url"
    fi
    
    # Get health check URL
    local health_url=$(terraform output -raw health_check_url 2>/dev/null || echo "")
    if [[ -n "$health_url" ]]; then
        echo "Health Check URL: $health_url"
    fi
    
    # Get CloudWatch dashboard URL
    local dashboard_url=$(terraform output -raw cloudwatch_dashboard_url 2>/dev/null || echo "")
    if [[ -n "$dashboard_url" ]]; then
        echo "CloudWatch Dashboard: $dashboard_url"
    fi
    
    echo ""
    log_success "Deployment information displayed"
}

main() {
    local env=$1
    shift
    
    # Parse options
    local skip_build=false
    local skip_push=false
    local skip_deploy=false
    local force_deploy=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                skip_build=true
                shift
                ;;
            --skip-push)
                skip_push=true
                shift
                ;;
            --skip-deploy)
                skip_deploy=true
                shift
                ;;
            --force-deploy)
                force_deploy=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Check if environment is provided
    if [[ -z "$env" ]]; then
        show_usage
        exit 1
    fi
    
    # Validate environment
    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $env"
        show_usage
        exit 1
    fi
    
    # Set default AWS region if not set
    export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-west-2}
    
    log_info "Starting complete deployment for Therapy Assistant Agent"
    log_info "Environment: $env"
    log_info "AWS Region: $AWS_DEFAULT_REGION"
    
    check_prerequisites
    
    # Confirm production deployments
    if [[ "$env" == "prod" ]]; then
        log_warning "You are about to deploy to PRODUCTION!"
        read -p "Are you sure? Type 'yes' to confirm: " -r
        if [[ $REPLY != "yes" ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Deploy infrastructure first if not skipping
    if [[ "$skip_deploy" != "true" ]]; then
        deploy_infrastructure "$env" "$force_deploy"
    fi
    
    # Get ECR repository URL
    local ecr_url=$(get_ecr_repository_url "$env")
    log_info "ECR Repository URL: $ecr_url"
    
    # Build Docker image if not skipping
    if [[ "$skip_build" != "true" ]]; then
        build_docker_image "$env"
    fi
    
    # Push Docker image if not skipping
    if [[ "$skip_push" != "true" ]]; then
        push_docker_image "$env" "$ecr_url"
    fi
    
    # Update ECS service to use new image
    update_ecs_service "$env"
    
    # Show deployment information
    show_deployment_info "$env"
    
    log_success "Complete deployment finished successfully!"
}

# Run main function
main "$@"