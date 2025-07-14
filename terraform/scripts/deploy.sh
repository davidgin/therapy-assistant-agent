#!/bin/bash

# Terraform Deployment Script for Therapy Assistant Agent
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh dev apply

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENVIRONMENTS_DIR="$PROJECT_ROOT/environments"

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
    echo "Usage: $0 [environment] [action]"
    echo ""
    echo "Environments:"
    echo "  dev       - Development environment"
    echo "  staging   - Staging environment"
    echo "  prod      - Production environment"
    echo ""
    echo "Actions:"
    echo "  plan      - Show what Terraform will do"
    echo "  apply     - Apply the Terraform configuration"
    echo "  destroy   - Destroy the infrastructure"
    echo "  output    - Show Terraform outputs"
    echo "  refresh   - Refresh Terraform state"
    echo ""
    echo "Examples:"
    echo "  $0 dev plan"
    echo "  $0 staging apply"
    echo "  $0 prod output"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials are not configured. Please configure AWS credentials first."
        exit 1
    fi
    
    # Check Terraform version
    TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
    log_info "Terraform version: $TERRAFORM_VERSION"
    
    # Check AWS CLI version
    AWS_VERSION=$(aws --version | awk '{print $1}' | cut -d'/' -f2)
    log_info "AWS CLI version: $AWS_VERSION"
    
    log_success "Prerequisites check passed"
}

validate_environment() {
    local env=$1
    
    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $env"
        show_usage
        exit 1
    fi
    
    local tfvars_file="$ENVIRONMENTS_DIR/$env/terraform.tfvars"
    if [[ ! -f "$tfvars_file" ]]; then
        log_error "Environment configuration file not found: $tfvars_file"
        exit 1
    fi
    
    log_info "Using environment: $env"
}

validate_action() {
    local action=$1
    
    if [[ ! "$action" =~ ^(plan|apply|destroy|output|refresh)$ ]]; then
        log_error "Invalid action: $action"
        show_usage
        exit 1
    fi
    
    log_info "Action: $action"
}

init_terraform() {
    local env=$1
    
    log_info "Initializing Terraform for environment: $env"
    
    cd "$PROJECT_ROOT"
    
    # Initialize Terraform
    terraform init \
        -backend-config="key=therapy-assistant-agent/$env/terraform.tfstate" \
        -backend-config="region=$AWS_DEFAULT_REGION"
    
    # Select or create workspace
    if terraform workspace list | grep -q "$env"; then
        terraform workspace select "$env"
    else
        terraform workspace new "$env"
    fi
    
    log_success "Terraform initialized for environment: $env"
}

run_terraform_action() {
    local env=$1
    local action=$2
    
    local tfvars_file="$ENVIRONMENTS_DIR/$env/terraform.tfvars"
    
    cd "$PROJECT_ROOT"
    
    case $action in
        plan)
            log_info "Running Terraform plan for environment: $env"
            terraform plan -var-file="$tfvars_file" -out="$env.tfplan"
            ;;
        apply)
            log_info "Running Terraform apply for environment: $env"
            
            # Check if plan file exists
            if [[ -f "$env.tfplan" ]]; then
                terraform apply "$env.tfplan"
            else
                log_warning "No plan file found. Running apply with auto-approve..."
                terraform apply -var-file="$tfvars_file" -auto-approve
            fi
            
            log_success "Terraform apply completed for environment: $env"
            
            # Show outputs
            log_info "Terraform outputs:"
            terraform output
            ;;
        destroy)
            log_warning "This will destroy all resources in the $env environment!"
            read -p "Are you sure? Type 'yes' to confirm: " -r
            if [[ $REPLY == "yes" ]]; then
                terraform destroy -var-file="$tfvars_file" -auto-approve
                log_success "Terraform destroy completed for environment: $env"
            else
                log_info "Destroy cancelled"
            fi
            ;;
        output)
            log_info "Terraform outputs for environment: $env"
            terraform output
            ;;
        refresh)
            log_info "Refreshing Terraform state for environment: $env"
            terraform refresh -var-file="$tfvars_file"
            log_success "Terraform state refreshed for environment: $env"
            ;;
    esac
}

main() {
    local env=$1
    local action=$2
    
    # Check if arguments are provided
    if [[ -z "$env" || -z "$action" ]]; then
        show_usage
        exit 1
    fi
    
    # Set default AWS region if not set
    export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-west-2}
    
    log_info "Starting Terraform deployment for Therapy Assistant Agent"
    log_info "Environment: $env"
    log_info "Action: $action"
    log_info "AWS Region: $AWS_DEFAULT_REGION"
    
    check_prerequisites
    validate_environment "$env"
    validate_action "$action"
    
    # Confirm production deployments
    if [[ "$env" == "prod" && "$action" == "apply" ]]; then
        log_warning "You are about to deploy to PRODUCTION!"
        read -p "Are you sure? Type 'yes' to confirm: " -r
        if [[ $REPLY != "yes" ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    init_terraform "$env"
    run_terraform_action "$env" "$action"
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"