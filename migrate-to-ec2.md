# Migration Guide: Docker/AWS to EC2 with GitHub Actions

This guide will help you migrate your Legal Document RAG System from Docker deployment on AWS to EC2 with GitHub Actions for CI/CD.

## Overview

The migration involves:
1. Setting up an EC2 instance
2. Configuring GitHub Actions for automated deployment
3. Moving from containerized deployment to native Python deployment
4. Setting up monitoring and backup systems

## Prerequisites

- AWS account with EC2 access
- GitHub repository for your project
- SSH key pair for EC2 access
- Domain name (optional, for SSL)

## Step 1: Create EC2 Instance

### 1.1 Launch EC2 Instance

1. Go to AWS EC2 Console
2. Launch a new instance with these specifications:
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance Type**: t3.medium or larger (recommended: t3.large for production)
   - **Storage**: At least 20GB GP3 SSD
   - **Security Group**: Allow SSH (22), HTTP (80), HTTPS (443)

### 1.2 Configure Security Group

Create a security group with these rules:
```
Type: SSH
Protocol: TCP
Port: 22
Source: Your IP (or 0.0.0.0/0 for any IP)

Type: HTTP
Protocol: TCP
Port: 80
Source: 0.0.0.0/0

Type: HTTPS
Protocol: TCP
Port: 443
Source: 0.0.0.0/0
```

### 1.3 Connect and Set Up

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Run the setup script
wget https://raw.githubusercontent.com/your-repo/document_rag/main/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh
```

## Step 2: Configure GitHub Repository

### 2.1 Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `EC2_INSTANCE_IP`: Your EC2 instance public IP
- `SSH_PRIVATE_KEY`: Your private SSH key content

### 2.2 Update .gitignore

Add these entries to your `.gitignore`:
```
# Environment files
.env
.env.local
.env.production

# Logs
*.log
logs/

# Database
chroma_db/
chroma_db_backup_*/

# Uploads
uploads/

# Python
__pycache__/
*.pyc
venv/
.venv/

# System
.DS_Store
```

## Step 3: Environment Configuration

### 3.1 Create Environment File

On your EC2 instance, create the environment file:

```bash
cd /opt/legal-rag-app
cp .env.template .env
nano .env
```

Fill in your actual values:
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-actual-secret-key

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
PRIVATE_GPT4_API_KEY=your-private-gpt4-api-key

# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Database Configuration
CHROMA_DB_PATH=./chroma_db

# Application Configuration
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=52428800
```

### 3.2 Set Up AWS Secrets Manager (Optional)

If you want to use AWS Secrets Manager instead of environment variables:

```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret --name legal-rag/secret-key --secret-string "your-secret-key"
aws secretsmanager create-secret --name legal-rag/anthropic-api-key --secret-string "your-anthropic-key"
aws secretsmanager create-secret --name legal-rag/openai-api-key --secret-string "your-openai-key"
aws secretsmanager create-secret --name legal-rag/private-gpt4-api-key --secret-string "your-private-gpt4-key"
```

## Step 4: Initial Deployment

### 4.1 Manual First Deployment

```bash
# On your EC2 instance
cd /opt/legal-rag-app

# Copy your application files
# (You can use scp, git clone, or copy from your local machine)

# Deploy
./deploy.sh

# Check status
./monitor.sh
```

### 4.2 Test the Application

```bash
# Check if the service is running
sudo systemctl status legal-rag

# Test the health endpoint
curl http://localhost:5001/health

# Check Nginx
sudo systemctl status nginx
curl http://your-ec2-ip/health
```

## Step 5: GitHub Actions Deployment

### 5.1 Push to GitHub

```bash
# Add the new files
git add .github/workflows/deploy.yml
git add ec2-setup.sh
git add migrate-to-ec2.md

# Commit and push
git commit -m "Add EC2 deployment with GitHub Actions"
git push origin main
```

### 5.2 Monitor Deployment

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Monitor the deployment workflow
4. Check the logs for any issues

## Step 6: SSL Certificate (Optional)

### 6.1 Set Up Domain

1. Point your domain to your EC2 instance IP
2. Update Nginx configuration with your domain name

### 6.2 Install SSL Certificate

```bash
# Install SSL certificate using Let's Encrypt
sudo certbot --nginx -d your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

## Step 7: Monitoring and Maintenance

### 7.1 Set Up Monitoring

The setup script creates several monitoring tools:

```bash
# Check application status
./monitor.sh

# View logs
sudo journalctl -u legal-rag -f

# Check system resources
htop
df -h
free -h
```

### 7.2 Backup Strategy

```bash
# Manual backup
./backup.sh

# Automatic backups run daily at 2 AM
# Check cron jobs
crontab -l
```

### 7.3 Update Process

1. Make changes to your code
2. Push to GitHub main branch
3. GitHub Actions automatically deploys to EC2
4. Monitor the deployment in GitHub Actions
5. Check application status on EC2

## Step 8: Clean Up Docker Resources

### 8.1 Remove Docker Resources

```bash
# Stop and remove ECS services
aws ecs update-service --cluster legal-rag-cluster --service legal-rag-service --desired-count 0
aws ecs delete-service --cluster legal-rag-cluster --service legal-rag-service

# Delete ECS cluster
aws ecs delete-cluster --cluster legal-rag-cluster

# Delete ECR repository
aws ecr delete-repository --repository-name legal-document-rag --force

# Delete task definitions
aws ecs deregister-task-definition --task-definition legal-rag-task
```

### 8.2 Remove Docker Files

You can now remove Docker-related files from your repository:
- `Dockerfile*`
- `docker-compose.yml`
- `deploy-aws.sh`
- `task-definition*.json`

## Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   # Check logs
   sudo journalctl -u legal-rag -f
   
   # Check environment
   cd /opt/legal-rag-app
   source venv/bin/activate
   python app.py
   ```

2. **Port conflicts**
   ```bash
   # Check what's using port 5001
   sudo netstat -tlnp | grep :5001
   
   # Kill conflicting process
   sudo pkill -f conflicting-process
   ```

3. **Permission issues**
   ```bash
   # Fix permissions
   sudo chown -R ubuntu:ubuntu /opt/legal-rag-app
   chmod +x /opt/legal-rag-app/*.sh
   ```

4. **GitHub Actions deployment fails**
   - Check SSH key format in GitHub secrets
   - Verify EC2 instance IP is correct
   - Check AWS credentials have proper permissions

### Performance Optimization

1. **Increase instance size** if needed
2. **Add more memory** for large document processing
3. **Use EBS optimized volumes** for better I/O
4. **Set up CloudWatch monitoring**

## Benefits of This Migration

1. **Faster deployments** - No Docker build time
2. **Easier debugging** - Direct access to logs and processes
3. **Cost effective** - No ECS overhead
4. **More control** - Direct server access
5. **Simpler architecture** - Fewer moving parts

## Next Steps

1. Set up monitoring alerts
2. Configure log aggregation
3. Set up staging environment
4. Implement blue-green deployments
5. Add performance monitoring

## Support

If you encounter issues during migration:
1. Check the logs: `sudo journalctl -u legal-rag -f`
2. Review GitHub Actions logs
3. Test locally before pushing
4. Use the monitoring script: `./monitor.sh`
