#!/bin/bash

# Quick Fix Script for Stuck AWS Deployment
# This script will clean up the stuck deployment and restart the service

set -e

# Configuration
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
REGION="ap-southeast-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "Starting stuck deployment fix..."

# Step 1: Stop all tasks
log "Stopping all running tasks..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --desired-count 0 \
    --region $REGION

success "Service scaled down to 0 tasks"

# Step 2: Wait for tasks to stop
log "Waiting for tasks to stop..."
sleep 60

# Step 3: Check if any tasks are still running
RUNNING_TASKS=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --desired-status RUNNING \
    --region $REGION \
    --query 'taskArns' \
    --output text)

if [ -n "$RUNNING_TASKS" ] && [ "$RUNNING_TASKS" != "None" ]; then
    warning "Some tasks are still running, forcing them to stop..."
    for task in $RUNNING_TASKS; do
        aws ecs stop-task \
            --cluster $CLUSTER_NAME \
            --task $task \
            --region $REGION
    done
    sleep 30
fi

# Step 4: Scale back up to 1 task
log "Scaling service back up to 1 task..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --desired-count 1 \
    --region $REGION

success "Service scaled up to 1 task"

# Step 5: Wait for new task to start
log "Waiting for new task to start..."
sleep 60

# Step 6: Check service status
log "Checking service status..."
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{status:status,runningCount:runningCount,pendingCount:pendingCount,desiredCount:desiredCount}'

# Step 7: Get latest task logs if available
log "Getting latest task logs..."
TASK_ARN=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --desired-status RUNNING \
    --region $REGION \
    --query 'taskArns[0]' \
    --output text)

if [ -n "$TASK_ARN" ] && [ "$TASK_ARN" != "None" ]; then
    TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)
    log "Latest task ID: $TASK_ID"
    
    # Get logs
    aws logs get-log-events \
        --log-group-name "/ecs/legal-rag-task" \
        --log-stream-name "ecs/legal-rag-app/$TASK_ID" \
        --region $REGION \
        --start-from-head \
        --limit 20
else
    warning "No running tasks found"
fi

success "Stuck deployment fix completed!"
log "The service should now be running with a fresh task."
