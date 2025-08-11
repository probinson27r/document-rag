#!/bin/bash

# Fix ALB Health Check Timeout
AWS_REGION="ap-southeast-2"

echo "🔧 Fixing ALB Health Check Timeout..."

# List all instances to see what's available
echo "📊 Available EC2 instances:"
aws ec2 describe-instances \
  --region $AWS_REGION \
  --query 'Reservations[].Instances[?State.Name==`running`].{InstanceId: InstanceId, Name: Tags[?Key==`Name`].Value|[0], VPC: VpcId, SecurityGroup: SecurityGroups[0].GroupId}' \
  --output table

# Get EC2 instance details (try multiple approaches)
echo "📊 Getting EC2 instance details..."
EC2_INFO=$(aws ec2 describe-instances \
  --region $AWS_REGION \
  --filters "Name=tag:Name,Values=*legal-rag*" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].{InstanceId: InstanceId, SecurityGroup: SecurityGroups[0].GroupId, VPC: VpcId, Subnet: SubnetId}' \
  --output json 2>/dev/null || echo "null")

if [ "$EC2_INFO" = "null" ] || [ "$EC2_INFO" = "" ]; then
    echo "❌ No EC2 instance found with 'legal-rag' in the name tag"
    echo "💡 Available instances:"
    aws ec2 describe-instances \
      --region $AWS_REGION \
      --filters "Name=instance-state-name,Values=running" \
      --query 'Reservations[].Instances[].{InstanceId: InstanceId, Name: Tags[?Key==`Name`].Value|[0], VPC: VpcId}' \
      --output table
    exit 1
fi

EC2_INSTANCE_ID=$(echo $EC2_INFO | jq -r '.InstanceId')
EC2_SG_ID=$(echo $EC2_INFO | jq -r '.SecurityGroup')
EC2_VPC_ID=$(echo $EC2_INFO | jq -r '.VPC')

echo "EC2 Instance: $EC2_INSTANCE_ID"
echo "EC2 Security Group: $EC2_SG_ID"
echo "EC2 VPC: $EC2_VPC_ID"

# List all load balancers to see what's available
echo "📊 Available Load Balancers:"
aws elbv2 describe-load-balancers \
  --region $AWS_REGION \
  --query 'LoadBalancers[].{Name: LoadBalancerName, DNS: DNSName, VPC: VpcId, Type: Type}' \
  --output table

# Get ALB details (try multiple approaches)
echo "📊 Getting ALB details..."
ALB_INFO=$(aws elbv2 describe-load-balancers \
  --region $AWS_REGION \
  --query 'LoadBalancers[?contains(LoadBalancerName, `legal-rag`)].{ARN: LoadBalancerArn, DNS: DNSName, SecurityGroup: SecurityGroups[0], VPC: VpcId}' \
  --output json 2>/dev/null || echo "[]")

if [ "$ALB_INFO" = "[]" ] || [ "$ALB_INFO" = "" ]; then
    echo "❌ No ALB found with 'legal-rag' in the name"
    echo "💡 Available load balancers:"
    aws elbv2 describe-load-balancers \
      --region $AWS_REGION \
      --query 'LoadBalancers[].{Name: LoadBalancerName, DNS: DNSName, VPC: VpcId}' \
      --output table
    exit 1
fi

ALB_ARN=$(echo $ALB_INFO | jq -r '.[0].ARN')
ALB_SG_ID=$(echo $ALB_INFO | jq -r '.[0].SecurityGroup')
ALB_VPC_ID=$(echo $ALB_INFO | jq -r '.[0].VPC')

echo "ALB ARN: $ALB_ARN"
echo "ALB Security Group: $ALB_SG_ID"
echo "ALB VPC: $ALB_VPC_ID"

# Check if VPCs match
if [ "$EC2_VPC_ID" != "$ALB_VPC_ID" ]; then
    echo "❌ ALB and EC2 are in different VPCs!"
    echo "EC2 VPC: $EC2_VPC_ID"
    echo "ALB VPC: $ALB_VPC_ID"
    exit 1
fi

# Fix security group rules
echo "🔧 Fixing security group rules..."

# Remove existing ALB rules (if any)
aws ec2 revoke-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 80 \
  --source-group $ALB_SG_ID \
  --region $AWS_REGION 2>/dev/null || true

aws ec2 revoke-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 443 \
  --source-group $ALB_SG_ID \
  --region $AWS_REGION 2>/dev/null || true

# Add new ALB rules
echo "Adding HTTP rule..."
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 80 \
  --source-group $ALB_SG_ID \
  --region $AWS_REGION

echo "Adding HTTPS rule..."
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 443 \
  --source-group $ALB_SG_ID \
  --region $AWS_REGION

# List all target groups to see what's available
echo "📊 Available Target Groups:"
aws elbv2 describe-target-groups \
  --region $AWS_REGION \
  --query 'TargetGroups[].{Name: TargetGroupName, Port: Port, Protocol: Protocol, VPC: VpcId}' \
  --output table

# Get target group
echo "📊 Getting target group..."
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
  --region $AWS_REGION \
  --query 'TargetGroups[?contains(TargetGroupName, `legal-rag`)].TargetGroupArn' \
  --output text 2>/dev/null || echo "")

if [ -z "$TARGET_GROUP_ARN" ]; then
    echo "❌ No target group found with 'legal-rag' in the name"
    echo "💡 Available target groups:"
    aws elbv2 describe-target-groups \
      --region $AWS_REGION \
      --query 'TargetGroups[].{Name: TargetGroupName, Port: Port, Protocol: Protocol}' \
      --output table
    exit 1
fi

echo "Target Group: $TARGET_GROUP_ARN"

# Update target group health check
echo "🔧 Updating health check settings..."
aws elbv2 modify-target-group \
  --target-group-arn $TARGET_GROUP_ARN \
  --health-check-path /health \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --health-check-interval-seconds 30 \
  --region $AWS_REGION

# Register EC2 instance with target group
echo "🔧 Registering EC2 with target group..."
aws elbv2 register-targets \
  --target-group-arn $TARGET_GROUP_ARN \
  --targets Id=$EC2_INSTANCE_ID \
  --region $AWS_REGION

echo "✅ ALB timeout fix completed!"
echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for health checks to update"
echo "2. Check target health: aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN --region $AWS_REGION"
echo "3. Test ALB: curl http://$(echo $ALB_INFO | jq -r '.[0].DNS')/health"
