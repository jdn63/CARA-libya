# CARA Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the CARA (Comprehensive Automated Risk Assessment) platform in production environments. CARA is designed for Wisconsin public health departments and requires specific configuration for optimal performance.

## System Requirements

### Production Environment
- **Python**: 3.11 or higher
- **Database**: PostgreSQL 13+ with PostGIS extension
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 50GB+ for data caching and logs
- **Network**: Stable internet connection for API data sources

### Dependencies
```bash
pip install -r requirements.txt
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file or set system environment variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/dbname

# Session Security
SESSION_SECRET=your-secure-random-secret-key-here

# API Keys (contact respective providers for access)
# Note: Census data now uses local CSV files for enhanced accuracy
AIRNOW_API_KEY=your-airnow-api-key

# Optional: Email Configuration
SENDGRID_API_KEY=your-sendgrid-key-for-notifications

# Application Configuration
FLASK_ENV=production
FLASK_DEBUG=False
```

### Secret Management Best Practices

1. **Never commit secrets to version control**
2. **Use environment-specific secret management:**
   - **Replit**: Use the secrets panel in the Replit IDE
   - **Cloud platforms**: Use managed secret services (AWS Secrets Manager, Azure Key Vault)
   - **On-premise**: Use environment files with restricted permissions

3. **Rotate secrets regularly** (quarterly recommended)
4. **Use different secrets per environment** (dev/staging/production)

## Database Setup

### PostgreSQL with PostGIS

```sql
-- Create database
CREATE DATABASE cara_production;

-- Enable PostGIS (run as superuser)
\c cara_production;
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

-- Create application user
CREATE USER cara_app WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE cara_production TO cara_app;
```

### Database Migrations

CARA uses Flask-SQLAlchemy for database management:

```bash
# Initialize database tables
python -c "from core import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with production settings
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --max-requests 1000 main:app
```

### Systemd Service (Linux)

Create `/etc/systemd/system/cara.service`:

```ini
[Unit]
Description=CARA Risk Assessment Platform
After=network.target

[Service]
Type=forking
User=cara
Group=cara
WorkingDirectory=/opt/cara
Environment=PATH=/opt/cara/venv/bin
EnvironmentFile=/opt/cara/.env
ExecStart=/opt/cara/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cara
sudo systemctl start cara
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

## Reverse Proxy Configuration

### Nginx Configuration

```nginx
upstream cara_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://cara_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/cara/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Logging Configuration

### Production Logging Setup

```python
# In your deployment script
import logging
from logging.handlers import RotatingFileHandler

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# Rotating file handler
handler = RotatingFileHandler('/var/log/cara/app.log', maxBytes=10000000, backupCount=5)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)

# Add handler to app logger
app.logger.addHandler(handler)
```

### Log Locations
- **Application logs**: `/var/log/cara/app.log`
- **Access logs**: `/var/log/cara/access.log`
- **Error logs**: `/var/log/cara/error.log`

## Monitoring and Health Checks

### Health Check Endpoint

CARA includes a built-in health check at `/health`:

```bash
curl http://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Monitoring Recommendations

1. **Application Performance Monitoring (APM)**
   - Use tools like New Relic, Datadog, or open-source alternatives
   - Monitor response times, error rates, and throughput

2. **Database Monitoring**
   - Track connection pool usage
   - Monitor query performance
   - Set up alerts for slow queries

3. **System Resources**
   - CPU and memory usage
   - Disk space (especially for data caching)
   - Network connectivity to external APIs

## Data Refresh Scheduling

CARA includes an automated data refresh scheduler:

### Scheduler Configuration

Edit `./data/config/scheduler_config.json`:

```json
{
  "refresh_intervals": {
    "weather_patterns": 3600,
    "disease_surveillance": 86400,
    "census_data": 604800
  },
  "max_retries": 3,
  "retry_delay": 300
}
```

### Manual Data Refresh

```bash
# Refresh all data sources
curl -X POST http://your-domain.com/admin/refresh-data

# Refresh specific data source
curl -X POST http://your-domain.com/admin/refresh-data/weather_patterns
```

## Backup and Recovery

### Database Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backup/cara"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -h localhost -U cara_app cara_production > "$BACKUP_DIR/cara_backup_$DATE.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "cara_backup_*.sql" -mtime +30 -delete
```

### Configuration Backups

Backup the following files/directories:
- `.env` file (without exposing secrets)
- `./data/config/` directory
- Custom configuration files

## Security Considerations

### Production Security Checklist

- [ ] **HTTPS enabled** with valid SSL certificates
- [ ] **Environment secrets secured** and not in version control
- [ ] **Database access restricted** to application server
- [ ] **Regular security updates** applied to OS and dependencies
- [ ] **Firewall configured** to allow only necessary ports
- [ ] **Regular backups tested** and verified
- [ ] **Monitoring and alerting configured**
- [ ] **Access logs reviewed** regularly

### Rate Limiting

Implement rate limiting for API endpoints:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify PostgreSQL is running
   - Check network connectivity

2. **API Key Issues**
   - Verify all required API keys are set
   - Check API key validity and quotas
   - Review API endpoint availability

3. **Memory Issues**
   - Monitor data cache usage
   - Adjust worker processes based on available memory
   - Implement cache cleanup policies

4. **Performance Issues**
   - Review database query performance
   - Check external API response times
   - Monitor system resource usage

### Log Analysis

```bash
# Check for errors in application logs
grep -i error /var/log/cara/app.log

# Monitor real-time logs
tail -f /var/log/cara/app.log

# Check scheduler status
grep "scheduler" /var/log/cara/app.log | tail -20
```

## Support and Maintenance

### Regular Maintenance Tasks

- **Weekly**: Review logs for errors and performance issues
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Rotate API keys and review access permissions
- **Annually**: Full system security audit and backup restoration test

### Support Contacts

For deployment support:
- **Technical Issues**: Contact Georgetown University research team
- **API Access**: Refer to individual API provider documentation
- **Wisconsin-Specific Data**: Contact Wisconsin Department of Health Services

---

*This deployment guide is maintained as part of the CARA platform documentation. Last updated: January 2024*