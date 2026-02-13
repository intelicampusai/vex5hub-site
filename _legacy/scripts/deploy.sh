#!/bin/bash
# Deploy script for 3150N Nighthawks Website
# Usage: ./deploy.sh [init|plan|apply|destroy|sync|invalidate]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform"
DIST_DIR="$PROJECT_ROOT/dist"
AWS_PROFILE="rdp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check AWS credentials
check_aws() {
    log_info "Checking AWS credentials for profile: $AWS_PROFILE"
    if ! aws sts get-caller-identity --profile "$AWS_PROFILE" > /dev/null 2>&1; then
        log_error "AWS credentials not configured for profile: $AWS_PROFILE"
        exit 1
    fi
    log_info "AWS credentials verified"
}

# Initialize Terraform
tf_init() {
    log_info "Initializing Terraform..."
    cd "$TERRAFORM_DIR"
    terraform init
}

# Plan Terraform changes
tf_plan() {
    log_info "Planning Terraform changes..."
    cd "$TERRAFORM_DIR"
    terraform plan
}

# Apply Terraform changes
tf_apply() {
    log_info "Applying Terraform changes..."
    cd "$TERRAFORM_DIR"
    terraform apply
}

# Destroy Terraform resources
tf_destroy() {
    log_warn "This will destroy all AWS resources!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        cd "$TERRAFORM_DIR"
        terraform destroy
    else
        log_info "Destroy cancelled"
    fi
}

# Sync website files to S3
sync_website() {
    log_info "Syncing website files to S3..."
    
    # Get bucket name from Terraform output
    cd "$TERRAFORM_DIR"
    BUCKET_NAME=$(terraform output -raw website_bucket_name 2>/dev/null || echo "")
    
    if [ -z "$BUCKET_NAME" ]; then
        log_error "Could not get bucket name. Have you run 'terraform apply'?"
        exit 1
    fi
    
    if [ ! -d "$DIST_DIR" ]; then
        log_error "Dist directory not found: $DIST_DIR"
        log_info "Build your website first, then run this command"
        exit 1
    fi
    
    log_info "Syncing to bucket: $BUCKET_NAME"
    aws s3 sync "$DIST_DIR" "s3://$BUCKET_NAME" --delete --profile "$AWS_PROFILE"
    
    log_info "Website sync complete"
}

# Invalidate CloudFront cache
invalidate_cache() {
    log_info "Invalidating CloudFront cache..."
    
    cd "$TERRAFORM_DIR"
    DIST_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
    
    if [ -z "$DIST_ID" ]; then
        log_error "Could not get CloudFront distribution ID. Have you run 'terraform apply'?"
        exit 1
    fi
    
    log_info "Invalidating distribution: $DIST_ID"
    aws cloudfront create-invalidation \
        --distribution-id "$DIST_ID" \
        --paths "/*" \
        --profile "$AWS_PROFILE"
    
    log_info "Cache invalidation initiated"
}

# Show deployment info
show_info() {
    cd "$TERRAFORM_DIR"
    
    echo ""
    log_info "=== Deployment Information ==="
    echo ""
    
    WEBSITE_URL=$(terraform output -raw website_url 2>/dev/null || echo "Not deployed")
    BUCKET_NAME=$(terraform output -raw website_bucket_name 2>/dev/null || echo "Not deployed")
    DIST_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "Not deployed")
    
    echo "Website URL:       $WEBSITE_URL"
    echo "S3 Bucket:        $BUCKET_NAME"
    echo "CloudFront ID:    $DIST_ID"
    echo ""
}

# Main command handler
case "${1:-help}" in
    init)
        check_aws
        tf_init
        ;;
    plan)
        check_aws
        tf_plan
        ;;
    apply)
        check_aws
        tf_apply
        show_info
        ;;
    destroy)
        check_aws
        tf_destroy
        ;;
    sync)
        check_aws
        sync_website
        invalidate_cache
        ;;
    invalidate)
        check_aws
        invalidate_cache
        ;;
    info)
        show_info
        ;;
    *)
        echo "Usage: $0 {init|plan|apply|destroy|sync|invalidate|info}"
        echo ""
        echo "Commands:"
        echo "  init       - Initialize Terraform"
        echo "  plan       - Preview infrastructure changes"
        echo "  apply      - Deploy AWS infrastructure"
        echo "  destroy    - Tear down all resources"
        echo "  sync       - Upload website files to S3"
        echo "  invalidate - Clear CloudFront cache"
        echo "  info       - Show deployment information"
        ;;
esac
