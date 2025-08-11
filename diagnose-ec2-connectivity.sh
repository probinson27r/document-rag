#!/bin/bash
# Diagnose EC2 SSH connectivity issues
# This script helps identify and fix common EC2 SSH connection problems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Diagnosing EC2 SSH Connectivity Issues..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS region
AWS_REGION=$(aws configure get region || echo "ap-southeast-2")
echo "🌏 AWS Region: $AWS_REGION"

echo ""
echo "1️⃣ Finding your EC2 instance..."

# Try to find instances with common names/tags
echo "Searching for Legal RAG related instances..."
INSTANCES=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,PrivateIpAddress,KeyName,Tags[?Key==`Name`].Value|[0]]' \
    --output table)

echo "$INSTANCES"

echo ""
echo "2️⃣ Checking for recent instance changes..."

# Get instances that were started in the last 24 hours
RECENT_INSTANCES=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[?LaunchTime>=`'$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)'`].[InstanceId,PublicIpAddress,State.Name,LaunchTime]' \
    --output table)

if [ -n "$RECENT_INSTANCES" ] && [ "$RECENT_INSTANCES" != "None" ]; then
    echo "Recent instances (started in last 24 hours):"
    echo "$RECENT_INSTANCES"
else
    echo "No instances started in the last 24 hours"
fi

echo ""
echo "3️⃣ Getting current IP addresses of running instances..."

# Get all running instances with their IPs
aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,PrivateIpAddress,KeyName]' \
    --output table

echo ""
echo "4️⃣ Checking GitHub Actions secrets..."

echo "📋 Your GitHub repository should have these secrets:"
echo "   EC2_INSTANCE_IP: The current public IP of your EC2 instance"
echo "   SSH_PRIVATE_KEY: Your private SSH key content"

echo ""
echo "5️⃣ Common issues and solutions:"
echo ""

echo -e "${YELLOW}🔄 Issue: Public IP changed after restart${NC}"
echo "   Solution: Update EC2_INSTANCE_IP secret in GitHub"
echo "   - Go to GitHub → Repository → Settings → Secrets and variables → Actions"
echo "   - Update EC2_INSTANCE_IP with the new public IP from above"

echo ""
echo -e "${YELLOW}🔐 Issue: SSH key mismatch${NC}"
echo "   Solution: Verify SSH key matches the EC2 instance key pair"
echo "   - Check KeyName in the table above"
echo "   - Ensure SSH_PRIVATE_KEY secret matches that key pair"

echo ""
echo -e "${YELLOW}🛡️ Issue: Security group blocks SSH${NC}"
echo "   Solution: Check security group allows SSH (port 22)"

echo ""
echo "6️⃣ Testing SSH connectivity..."

echo "Enter the public IP from the table above to test SSH:"
read -p "Public IP to test: " TEST_IP

if [ -n "$TEST_IP" ]; then
    echo "Testing SSH connectivity to $TEST_IP..."
    
    # Check if SSH port is open
    echo "Checking if port 22 is open..."
    if nc -z -w5 "$TEST_IP" 22 2>/dev/null; then
        echo -e "${GREEN}✅ Port 22 is open${NC}"
        
        echo "Now testing SSH key authentication..."
        echo "Note: You'll need your SSH private key file for this test"
        echo "Enter the path to your SSH private key (or press Enter to skip):"
        read -p "SSH key path: " SSH_KEY_PATH
        
        if [ -n "$SSH_KEY_PATH" ] && [ -f "$SSH_KEY_PATH" ]; then
            echo "Testing SSH connection..."
            if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "ubuntu@$TEST_IP" "echo 'SSH test successful'" 2>/dev/null; then
                echo -e "${GREEN}✅ SSH connection successful!${NC}"
                echo "Your instance is accessible at: ubuntu@$TEST_IP"
            else
                echo -e "${RED}❌ SSH connection failed${NC}"
                echo "Check:"
                echo "1. SSH key matches the instance key pair"
                echo "2. Security group allows SSH from your IP"
                echo "3. Instance is fully booted"
            fi
        else
            echo "Skipping SSH key test"
        fi
    else
        echo -e "${RED}❌ Port 22 is not accessible${NC}"
        echo "Check:"
        echo "1. Security group allows SSH (port 22) from your IP"
        echo "2. Instance is running and fully booted"
        echo "3. Network ACLs allow SSH traffic"
    fi
fi

echo ""
echo "🎯 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 📝 Update GitHub Secrets:"
echo "   - Go to: https://github.com/your-repo/document_rag/settings/secrets/actions"
echo "   - Update EC2_INSTANCE_IP with the correct public IP from above"
echo ""
echo "2. 🔄 Re-run GitHub Actions deployment:"
echo "   - Go to: https://github.com/your-repo/document_rag/actions"
echo "   - Click 'Re-run jobs' on the failed deployment"
echo ""
echo "3. 💡 Prevent future IP changes:"
echo "   - Consider allocating an Elastic IP address"
echo "   - aws ec2 allocate-address --region $AWS_REGION"
echo "   - aws ec2 associate-address --instance-id INSTANCE_ID --allocation-id ALLOCATION_ID"
echo ""
echo -e "${BLUE}💡 Tip: Elastic IP addresses prevent IP changes on restart and are free when attached to running instances.${NC}"
