# GitHub Actions Setup for AWS Container Deployment

This guide will help you set up GitHub Actions to automatically deploy your Legal Document RAG System to AWS ECS/ECR.

## Prerequisites

- GitHub repository with your code
- AWS account with ECS/ECR access
- AWS CLI configured locally
- Docker installed locally (for testing)

## Step 1: Create GitHub Repository

### Option A: Create New Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon → "New repository"
3. Name: `document-rag` or `legal-document-rag`
4. Make it Public or Private
5. **Don't** initialize with README (you already have files)
6. Click "Create repository"

### Option B: Use GitHub CLI
```bash
gh repo create document-rag --public --source=. --remote=origin --push
```

## Step 2: Add GitHub Remote

```bash
# Add the remote (replace with your actual repository URL)
git remote add origin https://github.com/YOUR_USERNAME/document-rag.git

# Push your code
git push -u origin main
```

## Step 3: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

### Required Secrets:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key

### Optional Secrets:
- `ALB_URL` - Your Application Load Balancer URL (for health checks)

### How to Get AWS Credentials:

#### Option A: IAM User
1. Go to AWS IAM Console
2. Create a new user or use existing
3. Attach policies:
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonECS-FullAccess`
   - `AmazonEC2ContainerServiceFullAccess`

#### Option B: IAM Role (Recommended for Production)
1. Create an IAM role with the policies above
2. Use AWS STS to get temporary credentials
3. Update the workflow to use role assumption

## Step 4: Verify AWS Resources

Make sure these AWS resources exist:

### ECR Repository
```bash
aws ecr create-repository --repository-name legal-document-rag --region ap-southeast-2
```

### ECS Cluster
```bash
aws ecs create-cluster --cluster-name legal-rag-cluster --region ap-southeast-2
```

### ECS Service
```bash
# This should already exist from your previous deployments
aws ecs describe-services --cluster legal-rag-cluster --services legal-rag-service --region ap-southeast-2
```

## Step 5: Test the Workflow

1. **Push to main branch** to trigger deployment
2. **Monitor the workflow** in GitHub Actions tab
3. **Check AWS Console** to verify deployment

## Step 6: Configure Environment Variables

Your application needs these environment variables in ECS:

### Required Environment Variables:
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
PRIVATE_GPT4_API_KEY=your-private-gpt4-key
```

### How to Set in ECS:
1. Go to ECS Console
2. Find your task definition
3. Edit the container definition
4. Add environment variables
5. Create new task definition revision
6. Update service

## Step 7: Set Up Secrets Manager (Recommended)

For better security, use AWS Secrets Manager:

### Create Secrets:
```bash
aws secretsmanager create-secret --name legal-rag/secret-key --secret-string "your-secret-key" --region ap-southeast-2
aws secretsmanager create-secret --name legal-rag/anthropic-api-key --secret-string "your-anthropic-key" --region ap-southeast-2
aws secretsmanager create-secret --name legal-rag/openai-api-key --secret-string "your-openai-key" --region ap-southeast-2
aws secretsmanager create-secret --name legal-rag/private-gpt4-api-key --secret-string "your-private-gpt4-key" --region ap-southeast-2
```

### Update Task Definition:
Add secrets to your task definition:
```json
{
  "secrets": [
    {
      "name": "SECRET_KEY",
      "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:ACCOUNT_ID:secret:legal-rag/secret-key"
    },
    {
      "name": "ANTHROPIC_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:ACCOUNT_ID:secret:legal-rag/anthropic-api-key"
    }
  ]
}
```

## Step 8: Monitoring and Alerts

### CloudWatch Alarms:
```bash
# Create alarms for your ECS service
aws cloudwatch put-metric-alarm \
  --alarm-name "ECS-Service-CPU-High" \
  --alarm-description "High CPU usage on ECS service" \
  --metric-name "CPUUtilization" \
  --namespace "AWS/ECS" \
  --statistic "Average" \
  --period 300 \
  --threshold 80 \
  --comparison-operator "GreaterThanThreshold" \
  --evaluation-periods 2 \
  --dimensions "Name=ClusterName,Value=legal-rag-cluster" "Name=ServiceName,Value=legal-rag-service" \
  --region ap-southeast-2
```

### GitHub Actions Notifications:
Add this to your workflow for notifications:
```yaml
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: 'Deployment Failed',
        body: 'Deployment to AWS ECS failed. Check the workflow logs for details.'
      })
```

## Troubleshooting

### Common Issues:

1. **ECR Login Failed**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Test ECR access
   aws ecr get-login-password --region ap-southeast-2
   ```

2. **ECS Service Not Found**
   ```bash
   # List services
   aws ecs list-services --cluster legal-rag-cluster --region ap-southeast-2
   
   # Create service if missing
   aws ecs create-service --cluster legal-rag-cluster --service-name legal-rag-service --task-definition legal-rag-task --desired-count 1 --region ap-southeast-2
   ```

3. **Task Definition Issues**
   ```bash
   # Describe task definition
   aws ecs describe-task-definition --task-definition legal-rag-task --region ap-southeast-2
   
   # Register new task definition
   aws ecs register-task-definition --cli-input-json file://task-definition.json --region ap-southeast-2
   ```

4. **Docker Build Fails**
   - Check Dockerfile syntax
   - Verify all files are present
   - Test build locally: `docker build -t test .`

### Debug Commands:
```bash
# Check ECS service status
aws ecs describe-services --cluster legal-rag-cluster --services legal-rag-service --region ap-southeast-2

# Check task status
aws ecs list-tasks --cluster legal-rag-cluster --service-name legal-rag-service --region ap-southeast-2

# Get task logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/legal-rag" --region ap-southeast-2
```

## Workflow Customization

### Environment-Specific Deployments:
```yaml
# Add environment-specific variables
env:
  AWS_REGION: ap-southeast-2
  ECR_REPOSITORY_NAME: legal-document-rag
  CLUSTER_NAME: ${{ github.ref == 'refs/heads/main' && 'legal-rag-prod' || 'legal-rag-staging' }}
  SERVICE_NAME: ${{ github.ref == 'refs/heads/main' && 'legal-rag-service-prod' || 'legal-rag-service-staging' }}
```

### Manual Deployment:
```yaml
# Add workflow_dispatch trigger
on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - staging
```

### Rollback Capability:
```yaml
# Add rollback job
rollback:
  runs-on: ubuntu-latest
  if: failure()
  steps:
  - name: Rollback to previous version
    run: |
      # Get previous task definition
      PREVIOUS_TASK_DEF=$(aws ecs describe-task-definition --task-definition legal-rag-task --region ap-southeast-2 --query 'taskDefinition.taskDefinitionArn' --output text)
      
      # Update service to use previous version
      aws ecs update-service --cluster legal-rag-cluster --service legal-rag-service --task-definition $PREVIOUS_TASK_DEF --region ap-southeast-2
```

## Security Best Practices

1. **Use IAM Roles** instead of access keys when possible
2. **Rotate credentials** regularly
3. **Use Secrets Manager** for sensitive data
4. **Enable CloudTrail** for audit logging
5. **Use VPC** for network isolation
6. **Enable encryption** for ECR images

## Cost Optimization

1. **Use Spot instances** for non-critical workloads
2. **Set up auto-scaling** based on demand
3. **Monitor resource usage** with CloudWatch
4. **Use lifecycle policies** for ECR images
5. **Consider Fargate Spot** for cost savings

This setup will give you automated deployments to AWS ECS with proper testing, monitoring, and rollback capabilities.
