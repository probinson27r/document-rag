#!/bin/bash

# List AWS Resources Script
AWS_REGION="ap-southeast-2"

echo "🔍 Listing AWS Resources in $AWS_REGION"
echo "========================================"

echo ""
echo "📊 EC2 Instances:"
aws ec2 describe-instances \
  --region $AWS_REGION \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].{InstanceId: InstanceId, Name: Tags[?Key==`Name`].Value|[0], Type: InstanceType, VPC: VpcId, SecurityGroup: SecurityGroups[0].GroupId}' \
  --output table

echo ""
echo "📊 Load Balancers:"
aws elbv2 describe-load-balancers \
  --region $AWS_REGION \
  --query 'LoadBalancers[].{Name: LoadBalancerName, DNS: DNSName, VPC: VpcId, Type: Type, State: State.Code}' \
  --output table

echo ""
echo "📊 Target Groups:"
aws elbv2 describe-target-groups \
  --region $AWS_REGION \
  --query 'TargetGroups[].{Name: TargetGroupName, Port: Port, Protocol: Protocol, VPC: VpcId, HealthPath: HealthCheckPath}' \
  --output table

echo ""
echo "📊 Security Groups:"
aws ec2 describe-security-groups \
  --region $AWS_REGION \
  --filters "Name=group-name,Values=*legal*" \
  --query 'SecurityGroups[].{Name: GroupName, ID: GroupId, VPC: VpcId, Description: Description}' \
  --output table

echo ""
echo "📊 VPCs:"
aws ec2 describe-vpcs \
  --region $AWS_REGION \
  --query 'Vpcs[].{VPC: VpcId, CIDR: CidrBlock, Name: Tags[?Key==`Name`].Value|[0], Default: IsDefault}' \
  --output table

echo ""
echo "💡 To fix the ALB timeout, you need:"
echo "1. An EC2 instance running your application"
echo "2. An Application Load Balancer"
echo "3. A Target Group pointing to your EC2 instance"
echo "4. Security groups allowing ALB → EC2 traffic"
echo ""
echo "🔧 Run: ./fix-alb-timeout.sh (after updating resource names if needed)"
