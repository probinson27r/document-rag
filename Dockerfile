# Use Amazon Linux 2023 with Python 3 for optimal AWS ECS Fargate compatibility
# This provides better performance, security updates, and integration with AWS services
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Set working directory
WORKDIR /app

# Install Python 3 and development tools (Amazon Linux 2023 uses python3 by default)
# Note: curl-minimal is pre-installed and sufficient for health checks
RUN dnf update -y && \
    dnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        gcc-c++ \
        git \
        make \
        pkg-config \
        && dnf clean all

# Create symbolic links for convenience
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads chroma_db

# Create a non-root user (Amazon Linux 2023 compatible)
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/status || exit 1

# Run the application with Python 3
CMD ["python3", "app.py"] 