# Deployment Guide

## Overview
This document provides step-by-step instructions for deploying the Sales Insight Automator to production environments.

---

## Pre-Deployment Checklist

**Infrastructure:**
- [ ] Docker and Docker Compose installed
- [ ] Sufficient server resources (2+ CPU, 2GB+ RAM)
- [ ] SSL certificate available (for HTTPS)
- [ ] Domain names configured

**Credentials:**
- [ ] Google Gemini API key obtained
- [ ] Gmail account with 2FA disabled OR app password generated
- [ ] GitHub account for CI/CD
- [ ] Deployment platform account (Vercel/Render)

**Configuration:**
- [ ] `.env` file created with all variables
- [ ] CORS origins updated for production domains
- [ ] Rate limits tuned for anticipated traffic
- [ ] Logging and monitoring setup

---

## Option 1: Vercel (Frontend) + Render (Backend)

### 1A. Deploy Frontend to Vercel

**Prerequisites:**
- Vercel account
- GitHub repository connected

**Steps:**

1. Log in to Vercel: https://vercel.com

2. Click "Add New..." → "Project"

3. Import the GitHub repository

4. Configure project settings:
   ```
   Framework: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   ```

5. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: `https://api.yourdomain.com`

6. Click "Deploy"

7. Verify deployment at provided URL

**Auto-Deploy on Push:**
Every push to `main` branch automatically triggers deployment.

---

### 1B. Deploy Backend to Render

**Prerequisites:**
- Render account
- GitHub repository

**Steps:**

1. Log in to Render: https://render.com

2. Click "New+" → "Web Service"

3. Connect GitHub repository and select `main` branch

4. Configure service:
   ```
   Name: sales-insight-backend
   Environment: Docker
   Region: Select closest region
   Plan: Standard (or higher for production)
   ```

5. Add environment variables:
   - `GOOGLE_API_KEY`: [Your Gemini API key]
   - `SENDER_EMAIL`: [Your email]
   - `SENDER_PASSWORD`: [Your app password]
   - `SMTP_SERVER`: smtp.gmail.com
   - `SMTP_PORT`: 587
   - `API_KEY_SECRET`: [Generate random string]
   - `CORS_ORIGINS`: https://your-frontend.vercel.app

6. Click "Create Web Service"

7. Monitor deployment in dashboard

**Custom Domain (Optional):**
1. Add custom domain in Render settings
2. Update DNS records
3. Enable auto SSL certificate

---

### Update Frontend to Point to Deployed Backend

Once backend is deployed on Render, update Vercel environment variables:
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

Redeploy from Vercel dashboard.

---

## Option 2: Self-Hosted Docker Deployment

### Prerequisites
- Linux server (Ubuntu 20.04+)
- Docker and Docker Compose installed
- Domain and SSL certificate

### 2A. Server Setup

```bash
# SSH into server
ssh ubuntu@your-server-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2B. Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-repo/sales-insight-automator.git
cd sales-insight-automator

# Create environment file
cp .env.example .env
nano .env  # Edit with your credentials

# Ensure correct permissions
chmod 600 .env
```

### 2C. SSL Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update paths in docker-compose.yml or nginx config
```

### 2D. Nginx Reverse Proxy Setup

Create `/etc/nginx/sites-available/sales-insight`:

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

Enable Nginx site:
```bash
sudo ln -s /etc/nginx/sites-available/sales-insight /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2E. Deploy with Docker Compose

```bash
# Build images (optional, compose auto-builds)
docker-compose build

# Start services
docker-compose up -d

# Verify services
docker-compose ps

# View logs
docker-compose logs -f

# Monitor health
watch -n 5 docker-compose ps
```

### 2F. Automated Backups & Updates

Create `/home/ubuntu/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/sales-insight"
mkdir -p $BACKUP_DIR
cd /home/ubuntu/sales-insight-automator

# Backup .env (Don't commit secrets!)
cp .env "$BACKUP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"

# Keep only last 7 days
find $BACKUP_DIR -name ".env.backup.*" -mtime +7 -delete

echo "Backup completed: $(date)" >> $HOME/backup.log
```

Set cron job:
```bash
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh
```

---

## Option 3: AWS Deployment (ECS + Fargate)

### Prerequisites
- AWS account with appropriate permissions
- AWS CLI configured
- ECR repositories created

### 3A. Build and Push Docker Images

```bash
# Set repository URLs
BACKEND_REPO="123456789.dkr.ecr.us-east-1.amazonaws.com/sales-insight-backend"
FRONTEND_REPO="123456789.dkr.ecr.us-east-1.amazonaws.com/sales-insight-frontend"

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $BACKEND_REPO

# Build and push backend
docker build -t $BACKEND_REPO:latest backend/
docker push $BACKEND_REPO:latest

# Build and push frontend
docker build -t $FRONTEND_REPO:latest frontend/
docker push $FRONTEND_REPO:latest
```

### 3B. Create ECS Task Definitions

See AWS documentation for detailed task definition JSON configuration.

### 3C. Deploy to ECS Fargate

```bash
# Create service
aws ecs create-service \
  --cluster production \
  --service-name sales-insight \
  --task-definition sales-insight:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

---

## Post-Deployment Validation

### 1. Health Checks

```bash
# Frontend
curl -I https://yourdomain.com
# Expected: 200 OK

# Backend
curl https://yourdomain.com/api/health
# Expected: {"status": "healthy", ...}

# API Docs
curl https://yourdomain.com/api/docs
# Expected: HTML Swagger UI
```

### 2. End-to-End Test

1. Navigate to frontend URL
2. Upload `sales_q1_2026.csv`
3. Enter test email
4. Verify summary sent within 60 seconds

### 3. Monitoring Setup

**DataDog / New Relic:**
```yaml
# docker-compose.yml
environment:
  - DD_API_KEY=${DATADOG_API_KEY}
  - DD_SITE=datadoghq.com
  - NEW_RELIC_APP_NAME=Sales Insight Automator
```

**CloudWatch (AWS):**
- Enable container logs
- Set up alarms for error rates
- Monitor API latency

### 4. Log Aggregation

```bash
# View production logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Or use managed service
# - AWS CloudWatch Logs
# - Sumo Logic
# - Splunk
# - ELK Stack
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple Instances)

**Load Balancer Configuration (AWS ALB):**
- Set up target groups for frontend and backend
- Configure auto-scaling policies
- Target: CPU util 70%, Memory 80%

**Database Scaling (if adding persistence):**
- Use RDS for managed database
- Enable read replicas
- Configure backups

### Vertical Scaling

```yaml
# Increase container resources
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Caching Strategy

Consider adding Redis for:
- Session storage
- Rate limit tracking
- Temporary summary results

```bash
# Add to docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

---

## Maintenance

### Update Application Code

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Verify
docker-compose ps
```

### Update Dependencies

```bash
# Python packages
pip install --upgrade -r backend/requirements.txt

# Node packages
cd frontend && npm update
```

### Certificate Renewal (Let's Encrypt)

```bash
# Auto-renew
sudo certbot renew --quiet

# Add to crontab:
# 0 3 * * * certbot renew --quiet && systemctl reload nginx
```

---

## Troubleshooting Deployment

### Service Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Verify environment variables
docker-compose config | grep -i "GOOGLE_API_KEY"

# Test API key
python3 -c "import google.generativeai; print('API OK')"
```

### High Memory Usage

```bash
# Check resource limits
docker stats

# Reduce container limits or add swap
dd if=/dev/zero of=/swapfile bs=1G count=4
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### Slow Response Times

```bash
# Profile API endpoints
docker exec sales-insight-backend python -m cProfile -s cumtime main.py

# Monitor network
docker exec sales-insight-backend iftop
```

---

## Emergency Procedures

### Rollback to Previous Version

```bash
# View deployment history
git log --oneline

# Rollback
git revert <commit-hash>
docker-compose down
docker-compose up -d --build
```

### Emergency Stop

```bash
# Stop all services
docker-compose down

# Remove volumes (CAREFUL - data loss)
docker-compose down -v
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

---

## Security Hardening Checklist

- [ ] Enable HTTPS/TLS
- [ ] Rotate API keys regularly
- [ ] Enable VPN for admin access
- [ ] Set up Web Application Firewall
- [ ] Configure DDoS protection
- [ ] Enable container scanning
- [ ] Regular security audits
- [ ] Penetration testing (3rd party)
- [ ] Incident response plan
- [ ] Disaster recovery plan

---

## Cost Optimization

**Vercel + Render:**
- Estimated: $15-50/month

**Self-Hosted (AWS EC2):**
- t3.small: ~$25/month
- Traffic: $0.02/GB

**AWS Fargate:**
- vCPU: $0.04/hour
- Memory: $0.0045/GB/hour
- Estimated: $50-150/month

---

**Last Updated:** March 2026  
**Questions?** Contact: devops@rabbitai.com
