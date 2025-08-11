#!/bin/bash
# Diagnose AWS Secrets Manager access issues on EC2
# This script helps identify why the application cannot access AWS secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Diagnosing AWS Secrets Manager Access..."

# Check if running on EC2
echo ""
echo "1️⃣ Checking if running on EC2..."
if curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Running on EC2 instance${NC}"
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    echo "   Instance ID: $INSTANCE_ID"
    
    # Get instance region
    AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
    echo "   Region: $AWS_REGION"
else
    echo -e "${RED}❌ Not running on EC2 or metadata service not accessible${NC}"
    AWS_REGION="ap-southeast-2"
    echo "   Using default region: $AWS_REGION"
fi

# Check IAM role attached to instance
echo ""
echo "2️⃣ Checking IAM instance profile..."
if curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/iam/security-credentials/ >/dev/null 2>&1; then
    ROLE_NAME=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    if [ -n "$ROLE_NAME" ]; then
        echo -e "${GREEN}✅ IAM role attached: $ROLE_NAME${NC}"
        
        # Check if we can get credentials
        if curl -s --connect-timeout 5 "http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Can access IAM credentials${NC}"
        else
            echo -e "${RED}❌ Cannot access IAM credentials${NC}"
        fi
    else
        echo -e "${RED}❌ No IAM role attached to instance${NC}"
        echo "   Need to attach IAM role with Secrets Manager permissions"
    fi
else
    echo -e "${RED}❌ Cannot access IAM metadata${NC}"
    echo "   Instance may not have IAM role or metadata service is blocked"
fi

# Check AWS CLI configuration
echo ""
echo "3️⃣ Checking AWS CLI configuration..."
if command -v aws >/dev/null 2>&1; then
    echo -e "${GREEN}✅ AWS CLI is installed${NC}"
    
    # Check if AWS CLI can get caller identity
    if aws sts get-caller-identity >/dev/null 2>&1; then
        echo -e "${GREEN}✅ AWS CLI can authenticate${NC}"
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
        echo "   Account ID: $ACCOUNT_ID"
        echo "   User/Role ARN: $USER_ARN"
    else
        echo -e "${RED}❌ AWS CLI cannot authenticate${NC}"
        echo "   Check IAM permissions or run 'aws configure'"
    fi
else
    echo -e "${RED}❌ AWS CLI not installed${NC}"
fi

# Check Python boto3 access
echo ""
echo "4️⃣ Checking Python boto3 access..."
if command -v python3 >/dev/null 2>&1; then
    python3 << EOF
import sys
try:
    import boto3
    print("✅ boto3 is available")
    
    try:
        session = boto3.session.Session()
        sts = session.client('sts', region_name='$AWS_REGION')
        response = sts.get_caller_identity()
        print(f"✅ boto3 can authenticate")
        print(f"   Account: {response['Account']}")
        print(f"   ARN: {response['Arn']}")
    except Exception as e:
        print(f"❌ boto3 cannot authenticate: {e}")
        
except ImportError:
    print("❌ boto3 not installed")
    sys.exit(1)
EOF
else
    echo -e "${RED}❌ Python3 not available${NC}"
fi

# Test Secrets Manager access
echo ""
echo "5️⃣ Testing Secrets Manager access..."

# List of secrets to test
secrets=("legal-rag/secret-key" "legal-rag/anthropic-api-key" "legal-rag/openai-api-key" "legal-rag/private-gpt4-api-key")

for secret in "${secrets[@]}"; do
    echo "   Testing: $secret"
    
    # Test with AWS CLI
    if command -v aws >/dev/null 2>&1; then
        if aws secretsmanager describe-secret --secret-id "$secret" --region "$AWS_REGION" >/dev/null 2>&1; then
            echo -e "     ${GREEN}✅ AWS CLI can access secret${NC}"
            
            # Try to get the actual value
            if aws secretsmanager get-secret-value --secret-id "$secret" --region "$AWS_REGION" --query SecretString --output text >/dev/null 2>&1; then
                echo -e "     ${GREEN}✅ AWS CLI can read secret value${NC}"
            else
                echo -e "     ${RED}❌ AWS CLI cannot read secret value${NC}"
            fi
        else
            echo -e "     ${RED}❌ AWS CLI cannot access secret (may not exist)${NC}"
        fi
    fi
    
    # Test with Python boto3
    if command -v python3 >/dev/null 2>&1; then
        python3 << EOF
import boto3
try:
    client = boto3.client('secretsmanager', region_name='$AWS_REGION')
    response = client.get_secret_value(SecretId='$secret')
    print("     ✅ Python boto3 can read secret value")
except Exception as e:
    print(f"     ❌ Python boto3 cannot read secret: {e}")
EOF
    fi
done

# Check environment variables as fallback
echo ""
echo "6️⃣ Checking environment variable fallbacks..."
env_vars=("PRIVATE_GPT4_API_KEY" "ANTHROPIC_API_KEY" "OPENAI_API_KEY" "SECRET_KEY")

for var in "${env_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo -e "   ${GREEN}✅ $var is set${NC}"
    else
        echo -e "   ${YELLOW}⚠️ $var is not set${NC}"
    fi
done

# Check application logs
echo ""
echo "7️⃣ Checking application logs for secrets-related errors..."
if systemctl is-active legal-rag >/dev/null 2>&1; then
    echo "   Recent logs from legal-rag service:"
    journalctl -u legal-rag --no-pager -n 10 | grep -i -E "(secret|aws|error|warning)" || echo "   No recent secrets-related log entries found"
else
    echo -e "${YELLOW}⚠️ legal-rag service is not running${NC}"
fi

echo ""
echo "🎯 Diagnosis Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate recommendations
echo ""
echo "📋 Recommendations:"

if [ -z "$ROLE_NAME" ]; then
    echo "1. ❗ Attach IAM role to EC2 instance:"
    echo "   - Run: ./setup-ec2-iam-secrets.sh"
    echo "   - Attach the created role to your EC2 instance"
fi

echo "2. 🔐 Create/verify AWS secrets:"
echo "   - Run: ./setup-aws-secrets.sh"

echo "3. 🔄 Alternative: Use environment variables:"
echo "   - Set PRIVATE_GPT4_API_KEY in /opt/legal-rag-app/.env"
echo "   - Or export directly in the shell before starting the app"

echo "4. 🔍 Check application startup:"
echo "   - sudo systemctl restart legal-rag"
echo "   - sudo journalctl -u legal-rag -f"

echo ""
echo -e "${BLUE}💡 The application will fall back to environment variables if AWS Secrets Manager access fails.${NC}"
