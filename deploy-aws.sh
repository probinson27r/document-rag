#!/bin/bash

# AWS Docker Deployment Script for Legal Document RAG System
# This script builds and deploys the application to AWS ECR/ECS

set -e

# Configuration
AWS_REGION="ap-southeast-2"  # Change to your preferred region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="legal-document-rag"
IMAGE_TAG="latest"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🚀 Starting AWS deployment for Legal Document RAG System..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION 2>/dev/null || echo "Repository already exists"

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image for ECS (linux/amd64 platform)
echo "🔨 Building Docker image for ECS (linux/amd64)..."
docker buildx build --platform linux/amd64 -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .

# Tag image for ECR
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG

echo "✅ Docker image pushed successfully!"
echo "📋 ECR Image URI: $ECR_URI:$IMAGE_TAG"

# Create ECS cluster if it doesn't exist
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION 2>/dev/null || echo "Cluster already exists"

# Create task definition
echo "📝 Creating ECS task definition..."
cat > task-definition.json << EOF
{
    "family": "$TASK_DEFINITION_NAME",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "legal-rag-app",
            "image": "$ECR_URI:$IMAGE_TAG",
            "portMappings": [
                {
                    "containerPort": 5001,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "FLASK_ENV",
                    "value": "production"
                }
            ],
            "secrets": [
                {
                    "name": "SECRET_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/secret-key"
                },
                {
                    "name": "ANTHROPIC_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/anthropic-api-key"
                },
                {
                    "name": "OPENAI_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/openai-api-key"
                },
                {
                    "name": "PRIVATE_GPT4_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/private-gpt4-api-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$TASK_DEFINITION_NAME",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:5001/api/status || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION

# Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/$TASK_DEFINITION_NAME" --region $AWS_REGION 2>/dev/null || echo "Log group already exists"

# Create ECS Task Execution Role
echo "🔐 Creating ECS Task Execution Role..."
ROLE_NAME="ecsTaskExecutionRole"

# Check if role already exists
if ! aws iam get-role --role-name $ROLE_NAME > /dev/null 2>&1; then
    echo "🆕 Creating IAM role: $ROLE_NAME"
    
    # Create the role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }'
    
    # Attach the AWS managed policy for ECS task execution
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    echo "✅ Created IAM role: $ROLE_NAME"
else
    echo "✅ IAM role already exists: $ROLE_NAME"
fi

echo "✅ Task definition created successfully!"

# Create Application Load Balancer
echo "🌐 Creating Application Load Balancer..."

# Create VPC if it doesn't exist (using default VPC)
echo "🔍 Checking for default VPC..."
DEFAULT_VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --region $AWS_REGION --query 'Vpcs[0].VpcId' --output text)

if [ "$DEFAULT_VPC_ID" = "None" ] || [ -z "$DEFAULT_VPC_ID" ]; then
    echo "❌ No default VPC found. Please create a VPC manually or specify a VPC ID."
    echo "💡 You can create a VPC using: aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region $AWS_REGION"
    exit 1
fi

echo "✅ Using default VPC: $DEFAULT_VPC_ID"

# Get subnets from default VPC
echo "🔍 Getting subnets from default VPC..."
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DEFAULT_VPC_ID" --region $AWS_REGION --query 'Subnets[*].SubnetId' --output text)

if [ -z "$SUBNETS" ]; then
    echo "❌ No subnets found in default VPC. Please create subnets manually."
    exit 1
fi

# Take first two subnets for ALB
SUBNET_IDS=$(echo $SUBNETS | tr ' ' '\n' | head -2 | tr '\n' ' ' | sed 's/ $//')
echo "✅ Using subnets: $SUBNET_IDS"

# Create security group for ALB
echo "🔒 Creating security group for ALB..."
ALB_SG_NAME="legal-rag-alb-sg"
ALB_SG_DESC="Security group for Legal Document RAG ALB"

# Check if security group already exists
EXISTING_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$ALB_SG_NAME" --region $AWS_REGION --query 'SecurityGroups[0].GroupId' --output text)

if [ "$EXISTING_SG" = "None" ] || [ -z "$EXISTING_SG" ]; then
    echo "🆕 Creating new security group: $ALB_SG_NAME"
    ALB_SG_ID=$(aws ec2 create-security-group \
        --group-name $ALB_SG_NAME \
        --description "$ALB_SG_DESC" \
        --vpc-id $DEFAULT_VPC_ID \
        --region $AWS_REGION \
        --query 'GroupId' --output text)
    
    # Add inbound rule for HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id $ALB_SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION
    
    echo "✅ Created security group: $ALB_SG_ID"
else
    ALB_SG_ID=$EXISTING_SG
    echo "✅ Using existing security group: $ALB_SG_ID"
fi

# Create security group for ECS tasks
echo "🔒 Creating security group for ECS tasks..."
ECS_SG_NAME="legal-rag-ecs-sg"
ECS_SG_DESC="Security group for Legal Document RAG ECS tasks"

# Check if security group already exists
EXISTING_ECS_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$ECS_SG_NAME" --region $AWS_REGION --query 'SecurityGroups[0].GroupId' --output text)

if [ "$EXISTING_ECS_SG" = "None" ] || [ -z "$EXISTING_ECS_SG" ]; then
    echo "🆕 Creating new security group: $ECS_SG_NAME"
    ECS_SG_ID=$(aws ec2 create-security-group \
        --group-name $ECS_SG_NAME \
        --description "$ECS_SG_DESC" \
        --vpc-id $DEFAULT_VPC_ID \
        --region $AWS_REGION \
        --query 'GroupId' --output text)
    
    # Add inbound rule from ALB
    aws ec2 authorize-security-group-ingress \
        --group-id $ECS_SG_ID \
        --protocol tcp \
        --port 5001 \
        --source-group $ALB_SG_ID \
        --region $AWS_REGION
    
    echo "✅ Created security group: $ECS_SG_ID"
else
    ECS_SG_ID=$EXISTING_ECS_SG
    echo "✅ Using existing security group: $ECS_SG_ID"
fi

# Create Application Load Balancer
ALB_NAME="legal-rag-alb"

# Check if ALB already exists
EXISTING_ALB=$(aws elbv2 describe-load-balancers --names $ALB_NAME --region $AWS_REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || echo "None")

if [ "$EXISTING_ALB" = "None" ] || [ -z "$EXISTING_ALB" ]; then
    echo "🆕 Creating new Application Load Balancer: $ALB_NAME"
    
    # Convert subnet IDs to proper array format for AWS CLI
    SUBNET_ARRAY=($SUBNET_IDS)
    
    ALB_ARN=$(aws elbv2 create-load-balancer \
        --name $ALB_NAME \
        --subnets "${SUBNET_ARRAY[@]}" \
        --security-groups $ALB_SG_ID \
        --scheme internet-facing \
        --type application \
        --region $AWS_REGION \
        --query 'LoadBalancers[0].LoadBalancerArn' --output text)
    
    echo "✅ Created ALB: $ALB_ARN"
else
    ALB_ARN=$EXISTING_ALB
    echo "✅ Using existing ALB: $ALB_ARN"
fi

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $AWS_REGION --query 'LoadBalancers[0].DNSName' --output text)
echo "🌍 ALB DNS Name: $ALB_DNS"

# Create target group
echo "🎯 Creating target group..."
TG_NAME="legal-rag-tg"

# Check if target group already exists
EXISTING_TG=$(aws elbv2 describe-target-groups --names $TG_NAME --region $AWS_REGION --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "None")

if [ "$EXISTING_TG" = "None" ] || [ -z "$EXISTING_TG" ]; then
    echo "🆕 Creating new target group: $TG_NAME"
    
    TG_ARN=$(aws elbv2 create-target-group \
        --name $TG_NAME \
        --protocol HTTP \
        --port 5001 \
        --vpc-id $DEFAULT_VPC_ID \
        --target-type ip \
        --health-check-protocol HTTP \
        --health-check-port 5001 \
        --health-check-path "/api/status" \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 2 \
        --region $AWS_REGION \
        --query 'TargetGroups[0].TargetGroupArn' --output text)
    
    echo "✅ Created target group: $TG_ARN"
else
    TG_ARN=$EXISTING_TG
    echo "✅ Using existing target group: $TG_ARN"
fi

# Create listener
echo "🎧 Creating ALB listener..."
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --region $AWS_REGION --query 'Listeners[0].ListenerArn' --output text 2>/dev/null || echo "None")

if [ "$LISTENER_ARN" = "None" ] || [ -z "$LISTENER_ARN" ]; then
    echo "🆕 Creating new listener on port 80"
    
    LISTENER_ARN=$(aws elbv2 create-listener \
        --load-balancer-arn $ALB_ARN \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn=$TG_ARN \
        --region $AWS_REGION \
        --query 'Listeners[0].ListenerArn' --output text)
    
    echo "✅ Created listener: $LISTENER_ARN"
else
    echo "✅ Using existing listener: $LISTENER_ARN"
fi

# Create ECS service with ALB integration
echo "🚀 Creating ECS service with ALB integration..."

# Check if service already exists
EXISTING_SERVICE=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].serviceArn' --output text 2>/dev/null || echo "None")

if [ "$EXISTING_SERVICE" = "None" ] || [ -z "$EXISTING_SERVICE" ]; then
    echo "🆕 Creating new ECS service: $SERVICE_NAME"
    
    # Convert subnet IDs to array format for ECS
    SUBNET_ARRAY_ECS=$(echo $SUBNET_IDS | sed 's/ /,/g')
    
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_DEFINITION_NAME:1 \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ARRAY_ECS],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" \
        --load-balancers "targetGroupArn=$TG_ARN,containerName=legal-rag-app,containerPort=5001" \
        --region $AWS_REGION
    
    echo "✅ Created ECS service: $SERVICE_NAME"
else
    echo "✅ ECS service already exists: $SERVICE_NAME"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Application Details:"
echo "- ALB DNS Name: http://$ALB_DNS"
echo "- Health Check: http://$ALB_DNS/api/status"
echo "- Application: http://$ALB_DNS"
echo ""
echo "📋 AWS Resources Created:"
echo "- ECS Cluster: $CLUSTER_NAME"
echo "- ECS Service: $SERVICE_NAME"
echo "- Task Definition: $TASK_DEFINITION_NAME"
echo "- Application Load Balancer: $ALB_NAME"
echo "- Target Group: $TG_NAME"
echo "- Security Groups: $ALB_SG_NAME, $ECS_SG_NAME"
echo ""
echo "🔗 Useful AWS Console links:"
echo "- ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo "- ECR Repository: https://console.aws.amazon.com/ecr/repositories/$ECR_REPOSITORY_NAME?region=$AWS_REGION"
echo "- Load Balancer: https://console.aws.amazon.com/ec2/v2/home?region=$AWS_REGION#LoadBalancer:loadBalancerArn=$ALB_ARN"
echo ""
echo "💡 Your application will be available at: http://$ALB_DNS"
echo "⏳ It may take a few minutes for the service to be fully ready." 