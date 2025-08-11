#!/bin/bash

# CloudWatch Setup Script for EC2 Legal Document RAG System
# This script sets up CloudWatch monitoring and alerting

set -e

# Configuration
AWS_REGION="ap-southeast-2"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
NAMESPACE="LegalDocumentRAG"

echo "📊 Setting up CloudWatch monitoring for Legal Document RAG System..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Install CloudWatch Agent
echo "📦 Installing CloudWatch Agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb

# Create CloudWatch Agent configuration
echo "🔧 Creating CloudWatch Agent configuration..."
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "agent": {
        "metrics_collection_interval": 60,
        "region": "$AWS_REGION",
        "debug": false
    },
    "metrics": {
        "namespace": "$NAMESPACE",
        "metrics_collected": {
            "cpu": {
                "resources": ["*"],
                "totalcpu": true,
                "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"]
            },
            "disk": {
                "resources": ["/"],
                "measurement": ["used_percent"]
            },
            "diskio": {
                "resources": ["*"],
                "measurement": ["io_time"]
            },
            "mem": {
                "measurement": ["mem_used_percent"]
            },
            "netstat": {
                "measurement": ["tcp_established", "tcp_time_wait"]
            },
            "swap": {
                "measurement": ["swap_used_percent"]
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/legal-rag-app/logs/app.log",
                        "log_group_name": "/opt/legal-rag-app/logs/app.log",
                        "log_stream_name": "$INSTANCE_ID",
                        "time_format": "%Y-%m-%d %H:%M:%S"
                    },
                    {
                        "file_path": "/opt/legal-rag-app/logs/monitor.log",
                        "log_group_name": "/opt/legal-rag-app/logs/monitor.log",
                        "log_stream_name": "$INSTANCE_ID",
                        "time_format": "%Y-%m-%d %H:%M:%S"
                    },
                    {
                        "file_path": "/var/log/nginx/access.log",
                        "log_group_name": "/var/log/nginx/access.log",
                        "log_stream_name": "$INSTANCE_ID"
                    },
                    {
                        "file_path": "/var/log/nginx/error.log",
                        "log_group_name": "/var/log/nginx/error.log",
                        "log_stream_name": "$INSTANCE_ID"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch Agent
echo "🚀 Starting CloudWatch Agent..."
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Enable CloudWatch Agent to start on boot
sudo systemctl enable amazon-cloudwatch-agent

# Create SNS Topic for alerts
echo "📢 Creating SNS Topic for alerts..."
SNS_TOPIC_ARN=$(aws sns create-topic \
    --name "Legal-Document-RAG-Alerts" \
    --region $AWS_REGION \
    --query 'TopicArn' \
    --output text)

echo "✅ SNS Topic created: $SNS_TOPIC_ARN"

# Create CloudWatch Alarms
echo "🚨 Creating CloudWatch Alarms..."

# CPU Utilization Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "Legal-RAG-High-CPU" \
    --alarm-description "High CPU utilization on Legal Document RAG instance" \
    --metric-name "CPUUtilization" \
    --namespace "AWS/EC2" \
    --statistic "Average" \
    --period 300 \
    --threshold 80 \
    --comparison-operator "GreaterThanThreshold" \
    --evaluation-periods 2 \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --dimensions "Name=InstanceId,Value=$INSTANCE_ID" \
    --region $AWS_REGION

# Memory Utilization Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "Legal-RAG-High-Memory" \
    --alarm-description "High memory utilization on Legal Document RAG instance" \
    --metric-name "mem_used_percent" \
    --namespace "$NAMESPACE" \
    --statistic "Average" \
    --period 300 \
    --threshold 85 \
    --comparison-operator "GreaterThanThreshold" \
    --evaluation-periods 2 \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --region $AWS_REGION

# Disk Space Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "Legal-RAG-High-Disk" \
    --alarm-description "High disk usage on Legal Document RAG instance" \
    --metric-name "disk_used_percent" \
    --namespace "$NAMESPACE" \
    --statistic "Average" \
    --period 300 \
    --threshold 90 \
    --comparison-operator "GreaterThanThreshold" \
    --evaluation-periods 2 \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --region $AWS_REGION

# Application Health Check Alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "Legal-RAG-Application-Down" \
    --alarm-description "Legal Document RAG application is down" \
    --metric-name "ApplicationHealth" \
    --namespace "$NAMESPACE" \
    --statistic "Sum" \
    --period 60 \
    --threshold 0 \
    --comparison-operator "LessThanThreshold" \
    --evaluation-periods 1 \
    --alarm-actions "$SNS_TOPIC_ARN" \
    --region $AWS_REGION

# Create CloudWatch Dashboard
echo "📊 Creating CloudWatch Dashboard..."
aws cloudwatch put-dashboard \
    --dashboard-name "Legal-Document-RAG-Monitoring" \
    --dashboard-body '{
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/EC2", "CPUUtilization", "InstanceId", "'$INSTANCE_ID'"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "'$AWS_REGION'",
                    "title": "CPU Utilization"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/EC2", "NetworkIn", "InstanceId", "'$INSTANCE_ID'"],
                        [".", "NetworkOut", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "'$AWS_REGION'",
                    "title": "Network Traffic"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["'$NAMESPACE'", "mem_used_percent"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "'$AWS_REGION'",
                    "title": "Memory Usage"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["'$NAMESPACE'", "disk_used_percent"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "'$AWS_REGION'",
                    "title": "Disk Usage"
                }
            }
        ]
    }' \
    --region $AWS_REGION

# Create custom metrics script
echo "📝 Creating custom metrics script..."
tee /opt/legal-rag-app/send-metrics.sh << 'EOF'
#!/bin/bash

# Send custom metrics to CloudWatch
NAMESPACE="LegalDocumentRAG"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

# Application health metric
aws cloudwatch put-metric-data \
    --namespace "$NAMESPACE" \
    --metric-data "MetricName=ApplicationHealth,Value=1,Unit=Count,Dimensions=InstanceId=$INSTANCE_ID" \
    --region ap-southeast-2

# Document processing time (example)
# aws cloudwatch put-metric-data \
#     --namespace "$NAMESPACE" \
#     --metric-data "MetricName=DocumentProcessingTime,Value=5.2,Unit=Seconds,Dimensions=InstanceId=$INSTANCE_ID" \
#     --region ap-southeast-2

# Active users (example)
# aws cloudwatch put-metric-data \
#     --namespace "$NAMESPACE" \
#     --metric-data "MetricName=ActiveUsers,Value=3,Unit=Count,Dimensions=InstanceId=$INSTANCE_ID" \
#     --region ap-southeast-2
EOF

chmod +x /opt/legal-rag-app/send-metrics.sh

# Add metrics sending to cron
echo "⏰ Adding metrics sending to cron..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/legal-rag-app/send-metrics.sh > /dev/null 2>&1") | crontab -

# Create log filter for error tracking
echo "🔍 Creating log filter for error tracking..."
aws logs put-metric-filter \
    --log-group-name "/opt/legal-rag-app/logs/app.log" \
    --filter-name "ErrorFilter" \
    --filter-pattern "ERROR" \
    --metric-transformations "MetricName=ErrorCount,Value=1,DefaultValue=0" \
    --region $AWS_REGION

# Create log filter for info tracking
aws logs put-metric-filter \
    --log-group-name "/opt/legal-rag-app/logs/app.log" \
    --filter-name "InfoFilter" \
    --filter-pattern "INFO" \
    --metric-transformations "MetricName=InfoCount,Value=1,DefaultValue=0" \
    --region $AWS_REGION

# Test CloudWatch Agent
echo "🧪 Testing CloudWatch Agent..."
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -m ec2 \
    -a status

# Send test metric
echo "📊 Sending test metric..."
aws cloudwatch put-metric-data \
    --namespace "$NAMESPACE" \
    --metric-data "MetricName=SetupComplete,Value=1,Unit=Count,Dimensions=InstanceId=$INSTANCE_ID" \
    --region $AWS_REGION

echo ""
echo "✅ CloudWatch monitoring setup completed!"
echo ""
echo "📋 Summary:"
echo "- CloudWatch Agent installed and configured"
echo "- SNS Topic created: $SNS_TOPIC_ARN"
echo "- CloudWatch Alarms created for CPU, Memory, Disk, and Application Health"
echo "- CloudWatch Dashboard created: Legal-Document-RAG-Monitoring"
echo "- Custom metrics script created: /opt/legal-rag-app/send-metrics.sh"
echo "- Log filters created for error and info tracking"
echo ""
echo "🔧 Useful commands:"
echo "- Check CloudWatch Agent status: sudo systemctl status amazon-cloudwatch-agent"
echo "- View CloudWatch logs: aws logs describe-log-groups --region $AWS_REGION"
echo "- View alarms: aws cloudwatch describe-alarms --region $AWS_REGION"
echo "- Send test metric: /opt/legal-rag-app/send-metrics.sh"
echo ""
echo "💡 Next steps:"
echo "1. Subscribe to SNS topic for alerts"
echo "2. Customize alarm thresholds as needed"
echo "3. Add more custom metrics to send-metrics.sh"
echo "4. Set up additional log filters for specific patterns"
