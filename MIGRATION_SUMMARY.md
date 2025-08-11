# Migration Summary: Docker/AWS to EC2 with GitHub Actions

## Overview

This document summarizes the complete migration plan from Docker deployment on AWS (ECS/ECR) to EC2 with GitHub Actions for your Legal Document RAG System.

## Why Migrate?

### Current Docker/AWS Setup Issues:
- **Slow deployments** - Docker build and push times
- **Complex debugging** - Containerized environment
- **ECS overhead** - Additional costs and complexity
- **Limited control** - Less direct access to the application

### Benefits of EC2 + GitHub Actions:
- **Faster deployments** - Direct code deployment
- **Easier debugging** - Direct server access
- **Cost effective** - No ECS overhead
- **More control** - Full server access
- **Simpler architecture** - Fewer moving parts

## Migration Components

### 1. Infrastructure Setup
- **EC2 Instance**: Ubuntu 22.04 LTS, t3.large recommended
- **Nginx**: Reverse proxy for the application
- **Systemd Service**: For application management
- **Security Groups**: SSH, HTTP, HTTPS access

### 2. CI/CD Pipeline
- **GitHub Actions**: Automated testing and deployment
- **Testing**: Run tests before deployment
- **Deployment**: Automated deployment to EC2
- **Health Checks**: Verify deployment success

### 3. Monitoring & Observability
- **CloudWatch Agent**: System and application metrics
- **Custom Metrics**: Application-specific monitoring
- **Alerts**: CPU, memory, disk, application health
- **Dashboard**: Centralized monitoring view

### 4. Backup & Maintenance
- **Automated Backups**: Daily backups with retention
- **Log Rotation**: Automatic log management
- **Monitoring Scripts**: Health check automation

## Files Created

### Core Migration Files:
1. **`.github/workflows/deploy.yml`** - GitHub Actions deployment workflow
2. **`ec2-setup.sh`** - EC2 instance setup script
3. **`migrate-to-ec2.md`** - Detailed migration guide
4. **`cleanup-docker.sh`** - Docker resources cleanup script

### Monitoring Files:
5. **`setup-cloudwatch.sh`** - CloudWatch monitoring setup
6. **`ec2-monitoring.yml`** - Monitoring configuration template

## Migration Steps

### Phase 1: Preparation
1. **Create EC2 Instance**
   - Launch Ubuntu 22.04 LTS instance
   - Configure security groups
   - Set up SSH access

2. **Set Up GitHub Repository**
   - Add GitHub secrets for deployment
   - Update `.gitignore` for EC2 deployment
   - Push migration files

### Phase 2: EC2 Setup
3. **Run EC2 Setup Script**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   wget https://raw.githubusercontent.com/your-repo/document_rag/main/ec2-setup.sh
   chmod +x ec2-setup.sh
   ./ec2-setup.sh
   ```

4. **Configure Environment**
   - Create `.env` file with API keys
   - Set up AWS credentials
   - Configure application settings

### Phase 3: Initial Deployment
5. **Manual First Deployment**
   ```bash
   cd /opt/legal-rag-app
   ./deploy.sh
   ./monitor.sh
   ```

6. **Test Application**
   - Verify health endpoint
   - Test document upload
   - Check all functionality

### Phase 4: Automated Deployment
7. **Push to GitHub**
   - Commit and push changes
   - Monitor GitHub Actions
   - Verify automated deployment

### Phase 5: Monitoring Setup
8. **Set Up CloudWatch**
   ```bash
   ./setup-cloudwatch.sh
   ```

9. **Configure Alerts**
   - Subscribe to SNS topic
   - Customize alarm thresholds
   - Test alerting

### Phase 6: Cleanup
10. **Remove Docker Resources**
    ```bash
    ./cleanup-docker.sh
    ```

11. **Remove Docker Files**
    - Delete Dockerfiles
    - Remove docker-compose.yml
    - Clean up deployment scripts

## Configuration Requirements

### GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `EC2_INSTANCE_IP`
- `SSH_PRIVATE_KEY`

### Environment Variables:
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
PRIVATE_GPT4_API_KEY=your-private-gpt4-key
AWS_REGION=ap-southeast-2
```

## Monitoring & Alerts

### CloudWatch Metrics:
- **System Metrics**: CPU, memory, disk, network
- **Application Metrics**: Health checks, response times
- **Custom Metrics**: Document processing, user activity

### Alerts:
- **High CPU** (>80% for 5 minutes)
- **High Memory** (>85% for 5 minutes)
- **High Disk** (>90% for 5 minutes)
- **Application Down** (health check fails)

### Dashboard:
- Real-time system metrics
- Application performance
- Error tracking
- Resource utilization

## Maintenance Tasks

### Daily:
- Monitor application logs
- Check system resources
- Verify backup completion

### Weekly:
- Review CloudWatch metrics
- Update dependencies
- Check security updates

### Monthly:
- Review and optimize performance
- Update monitoring thresholds
- Plan capacity upgrades

## Troubleshooting Guide

### Common Issues:

1. **Application Won't Start**
   ```bash
   sudo journalctl -u legal-rag -f
   cd /opt/legal-rag-app
   source venv/bin/activate
   python app.py
   ```

2. **Deployment Fails**
   - Check GitHub Actions logs
   - Verify SSH key format
   - Check EC2 instance connectivity

3. **High Resource Usage**
   - Monitor with `htop`
   - Check application logs
   - Consider instance upgrade

4. **SSL Certificate Issues**
   ```bash
   sudo certbot --nginx -d your-domain.com
   sudo certbot renew --dry-run
   ```

## Cost Comparison

### Docker/AWS (Monthly):
- ECS Fargate: ~$50-100
- ECR Storage: ~$5-10
- Load Balancer: ~$20
- **Total: ~$75-130**

### EC2 + GitHub Actions (Monthly):
- EC2 t3.large: ~$30-40
- EBS Storage: ~$5-10
- CloudWatch: ~$5-10
- **Total: ~$40-60**

**Savings: ~35-50%**

## Security Considerations

### Network Security:
- Security groups with minimal access
- SSH key-based authentication
- HTTPS with Let's Encrypt

### Application Security:
- Environment variable management
- Regular security updates
- Access logging and monitoring

### Data Security:
- Encrypted backups
- Secure API key storage
- Regular security audits

## Performance Optimization

### Instance Sizing:
- **Development**: t3.medium
- **Production**: t3.large or t3.xlarge
- **High Load**: c5.large or c5.xlarge

### Application Optimization:
- Nginx reverse proxy
- Gzip compression
- Static file caching
- Database optimization

### Monitoring Optimization:
- Custom metrics for business KPIs
- Performance baselines
- Capacity planning

## Rollback Plan

### If Migration Fails:
1. **Keep Docker resources** until EC2 is stable
2. **Maintain both environments** during transition
3. **Test thoroughly** before cleanup
4. **Document rollback procedures**

### Rollback Steps:
1. Scale up ECS service
2. Update DNS/load balancer
3. Verify application health
4. Investigate migration issues

## Success Criteria

### Technical:
- [ ] Application deploys successfully via GitHub Actions
- [ ] All functionality works on EC2
- [ ] Monitoring and alerts are active
- [ ] Performance meets or exceeds Docker deployment

### Operational:
- [ ] Deployment time reduced by 50%+
- [ ] Debugging capabilities improved
- [ ] Cost savings achieved
- [ ] Monitoring provides better visibility

### Business:
- [ ] No downtime during migration
- [ ] All features remain functional
- [ ] User experience maintained or improved
- [ ] Support team can manage new environment

## Next Steps

### Immediate (Week 1):
1. Create EC2 instance
2. Run setup scripts
3. Test manual deployment
4. Set up monitoring

### Short-term (Week 2-3):
1. Configure GitHub Actions
2. Test automated deployment
3. Set up alerts
4. Performance testing

### Medium-term (Month 1-2):
1. Clean up Docker resources
2. Optimize performance
3. Set up staging environment
4. Document procedures

### Long-term (Month 3+):
1. Consider auto-scaling
2. Implement blue-green deployments
3. Add advanced monitoring
4. Plan for multi-region deployment

## Support & Resources

### Documentation:
- [Migration Guide](migrate-to-ec2.md)
- [EC2 Setup Script](ec2-setup.sh)
- [CloudWatch Setup](setup-cloudwatch.sh)

### Monitoring:
- CloudWatch Dashboard
- Application logs
- System metrics
- Custom alerts

### Maintenance:
- Automated backups
- Log rotation
- Security updates
- Performance monitoring

This migration provides a more efficient, cost-effective, and maintainable deployment strategy for your Legal Document RAG System while maintaining all existing functionality and improving operational capabilities.
