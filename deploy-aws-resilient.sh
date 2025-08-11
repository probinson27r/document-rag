#!/bin/bash

# Resilient AWS Deployment Script for Legal Document RAG
# This script includes comprehensive error handling, retry logic, and health checks

set -e  # Exit on any error

# Configuration
ECR_REPO="199279692978.dkr.ecr.ap-southeast-2.amazonaws.com/legal-document-rag"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
REGION="ap-southeast-2"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to retry a command
retry_command() {
    local cmd="$1"
    local max_attempts="${2:-3}"
    local delay="${3:-10}"
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "Attempt $attempt/$max_attempts: $cmd"
        
        if eval "$cmd"; then
            success "Command succeeded on attempt $attempt"
            return 0
        else
            error "Command failed on attempt $attempt"
            if [ $attempt -lt $max_attempts ]; then
                warning "Retrying in $delay seconds..."
                sleep $delay
            fi
        fi
        ((attempt++))
    done
    
    error "Command failed after $max_attempts attempts"
    return 1
}

# Function to check AWS CLI configuration
check_aws_config() {
    log "Checking AWS CLI configuration..."
    
    if ! command_exists aws; then
        error "AWS CLI is not installed"
        exit 1
    fi
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        error "AWS CLI is not configured or credentials are invalid"
        exit 1
    fi
    
    success "AWS CLI configuration verified"
}

# Function to check Docker
check_docker() {
    log "Checking Docker..."
    
    if ! command_exists docker; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    success "Docker is ready"
}

# Function to build Docker image
build_image() {
    log "Building Docker image for AWS ECS (linux/amd64)..."
    
    # Clean up any existing images to prevent conflicts
    docker system prune -f
    
    # Build with explicit platform for ECS compatibility
    retry_command "docker buildx build --platform linux/amd64 -t ${ECR_REPO}:${IMAGE_TAG} ." 3 30
    
    success "Docker image built successfully"
}

# Function to authenticate with ECR
authenticate_ecr() {
    log "Authenticating with ECR..."
    
    retry_command "aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_REPO}" 3 10
    
    success "ECR authentication successful"
}

# Function to push Docker image
push_image() {
    log "Pushing Docker image to ECR..."
    
    retry_command "docker push ${ECR_REPO}:${IMAGE_TAG}" 3 30
    
    success "Docker image pushed successfully"
}

# Function to check ECS service status
check_service_status() {
    local service_status
    service_status=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $REGION \
        --query 'services[0].status' \
        --output text 2>/dev/null || echo "UNKNOWN")
    
    echo "$service_status"
}

# Function to wait for service stability
wait_for_service_stability() {
    log "Waiting for ECS service to become stable..."
    
    local max_wait_time=900  # 15 minutes
    local wait_time=0
    local check_interval=30
    
    while [ $wait_time -lt $max_wait_time ]; do
        local status
        status=$(aws ecs describe-services \
            --cluster $CLUSTER_NAME \
            --services $SERVICE_NAME \
            --region $REGION \
            --query 'services[0].deployments[0].rolloutState' \
            --output text 2>/dev/null || echo "UNKNOWN")
        
        log "Service rollout state: $status"
        
        if [ "$status" = "COMPLETED" ]; then
            success "Service deployment completed successfully"
            return 0
        elif [ "$status" = "FAILED" ]; then
            error "Service deployment failed"
            return 1
        elif [ "$status" = "IN_PROGRESS" ]; then
            log "Service deployment still in progress..."
        else
            warning "Unknown service state: $status"
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done
    
    error "Service did not become stable within $max_wait_time seconds"
    return 1
}

# Function to check service health
check_service_health() {
    log "Checking service health..."
    
    # Get the ALB DNS name
    local alb_dns
    alb_dns=$(aws elbv2 describe-load-balancers \
        --region $REGION \
        --query 'LoadBalancers[?contains(LoadBalancerName, `legal-rag`)].DNSName' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$alb_dns" ]; then
        warning "Could not find ALB DNS name, skipping health check"
        return 0
    fi
    
    log "ALB DNS: $alb_dns"
    
    # Wait for the service to be ready
    sleep 60
    
    # Test health endpoint
    retry_command "curl -f -k https://${alb_dns}/health" 5 30
    
    success "Service health check passed"
}

# Function to force new deployment
force_new_deployment() {
    log "Forcing new deployment..."
    
    retry_command "aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --force-new-deployment \
        --region $REGION" 3 10
    
    success "New deployment forced"
}

# Function to rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    # Get the previous task definition
    local current_task_def
    current_task_def=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $REGION \
        --query 'services[0].taskDefinition' \
        --output text)
    
    local task_family
    task_family=$(echo $current_task_def | cut -d':' -f1)
    
    # Get the previous revision
    local previous_revision
    previous_revision=$(aws ecs describe-task-definition \
        --task-definition $current_task_def \
        --region $REGION \
        --query 'taskDefinition.revision' \
        --output text)
    
    local rollback_revision=$((previous_revision - 1))
    
    if [ $rollback_revision -gt 0 ]; then
        log "Rolling back to task definition revision $rollback_revision"
        
        retry_command "aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service $SERVICE_NAME \
            --task-definition ${task_family}:${rollback_revision} \
            --region $REGION" 3 10
        
        success "Rollback initiated"
    else
        error "No previous revision available for rollback"
        return 1
    fi
}

# Function to get service logs
get_service_logs() {
    log "Getting recent service logs..."
    
    local log_group="/ecs/legal-rag-task"
    
    # Get the latest log stream
    local latest_stream
    latest_stream=$(aws logs describe-log-streams \
        --log-group-name "$log_group" \
        --region $REGION \
        --order-by LastEventTime \
        --descending \
        --max-items 1 \
        --query 'logStreams[0].logStreamName' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$latest_stream" ] && [ "$latest_stream" != "None" ]; then
        log "Latest log stream: $latest_stream"
        aws logs get-log-events \
            --log-group-name "$log_group" \
            --log-stream-name "$latest_stream" \
            --region $REGION \
            --start-from-head \
            --limit 50
    else
        warning "No log streams found"
    fi
}

# Main deployment function
main() {
    log "Starting resilient AWS deployment..."
    
    # Pre-flight checks
    check_aws_config
    check_docker
    
    # Build and push
    build_image
    authenticate_ecr
    push_image
    
    # Deploy
    force_new_deployment
    
    # Wait for stability
    if wait_for_service_stability; then
        # Check health
        if check_service_health; then
            success "Deployment completed successfully!"
            log "Service is healthy and ready"
        else
            error "Service health check failed"
            get_service_logs
            exit 1
        fi
    else
        error "Service deployment failed"
        get_service_logs
        
        # Attempt rollback
        log "Attempting rollback..."
        if rollback_deployment; then
            warning "Rollback completed. Please investigate the deployment issues."
        else
            error "Rollback failed. Manual intervention required."
        fi
        
        exit 1
    fi
}

# Handle script interruption
trap 'error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
