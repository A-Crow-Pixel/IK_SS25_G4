# Deployment Guide

## 📋 Overview

This document provides a complete deployment guide for the Internetkommunikation_Project_Gruppe4 chat application, including deployment methods for development, testing, and production environments.

## 🛠️ Environment Requirements

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python Version**: 3.8+
- **Memory**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 1GB available space
- **Network**: Support for TCP/UDP communication

### Software Dependencies
- Python 3.8+
- pip (Python package manager)
- Git (version control)

## 🔧 Installation Steps

### 1. Clone Project
```bash
git clone https://gitlab.lrz.de/00000000014AEF26/internetkommunikation_project_gruppe4.git
cd internetkommunikation_project_gruppe4
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
# Check Python version
python --version

# Check dependency packages
pip list
```

## 🚀 Development Environment Deployment

### Quick Start
```bash
# Start server
python run_server.py

# Start client (new terminal)
python run_client.py
```

### Development Mode Configuration
```bash
# Set development environment variables
export INTERCHAT_ENV=development
export INTERCHAT_DEBUG=true

# Windows
set INTERCHAT_ENV=development
set INTERCHAT_DEBUG=true
```

### Debug Configuration
```python
# Enable debugging in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🧪 Testing Environment Deployment

### Test Server Configuration
```bash
# Start test server
python server/server.py \
  --serverid TestServer \
  --udpport 9999 \
  --tcpport 65433 \
  --log-level DEBUG
```

### Multi-Server Testing
```bash
# Server 1
python server/server.py --serverid Server_1 --udpport 9999 --tcpport 65433

# Server 2
python server/server.py --serverid Server_2 --udpport 9998 --tcpport 65434

# Server 3
python server/server.py --serverid Server_3 --udpport 9997 --tcpport 65435
```

### Load Testing
```bash
# Start multiple clients for load testing
for i in {1..10}; do
    python client/client.py &
done
```

## 🏭 Production Environment Deployment

### 1. Server Preparation

#### System Requirements
- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM
- **Storage**: 20GB+ available space
- **Network**: Stable internet connection
- **OS**: Ubuntu 20.04+ (recommended)

#### Security Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install firewall
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 65433 # TCP port
sudo ufw allow 9999  # UDP port
```

### 2. Application Deployment

#### Create Application Directory
```bash
sudo mkdir -p /opt/internetkommunikation
sudo chown $USER:$USER /opt/internetkommunikation
cd /opt/internetkommunikation
```

#### Deploy Code
```bash
# Clone project
git clone https://gitlab.lrz.de/00000000014AEF26/internetkommunikation_project_gruppe4.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Create Configuration
```bash
# Create configuration file
cat > config.py << EOF
# Production environment configuration
PRODUCTION = True
DEBUG = False
LOG_LEVEL = 'INFO'

# Server configuration
DEFAULT_SERVER_ID = 'ProductionServer'
DEFAULT_UDP_PORT = 9999
DEFAULT_TCP_PORT = 65433

# Database configuration (if needed)
DATABASE_URL = 'sqlite:///internetkommunikation.db'

# Log configuration
LOG_FILE = '/var/log/internetkommunikation/server.log'
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
EOF
```

### 3. System Service Setup

#### Create System Service
**systemd service file** (`/etc/systemd/system/internetkommunikation-server.service`):
```ini
[Unit]
Description=Internetkommunikation Project Gruppe4 Server
After=network.target

[Service]
Type=simple
User=interchat
Group=interchat
WorkingDirectory=/opt/internetkommunikation
Environment=PATH=/opt/internetkommunikation/venv/bin
ExecStart=/opt/internetkommunikation/venv/bin/python server/server.py --serverid ProductionServer --udpport 9999 --tcpport 65433
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Setup Service
```bash
# Create user
sudo useradd -r -s /bin/false interchat
sudo chown -R interchat:interchat /opt/internetkommunikation

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable internetkommunikation-server
sudo systemctl start internetkommunikation-server

# Check status
sudo systemctl status internetkommunikation-server
```

### 4. Logging Configuration

#### Setup Logging
```bash
# Create log directory
sudo mkdir -p /var/log/internetkommunikation
sudo chown interchat:interchat /var/log/internetkommunikation

# Configure logrotate
sudo tee /etc/logrotate.d/internetkommunikation << EOF
/var/log/internetkommunikation/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 interchat interchat
    postrotate
        systemctl reload internetkommunikation-server
    endscript
}
EOF
```

### 5. Monitoring Setup

#### Create Monitoring Script
```bash
# Create monitoring script
cat > /opt/internetkommunikation/monitor.sh << 'EOF'
#!/bin/bash

# Check service status
if ! systemctl is-active --quiet internetkommunikation-server; then
    echo "$(date): Internetkommunikation server is down, restarting..." >> /var/log/internetkommunikation/monitor.log
    systemctl restart internetkommunikation-server
fi

# Check memory usage
MEMORY_USAGE=$(ps aux | grep "python.*server.py" | grep -v grep | awk '{print $4}')
if [ ! -z "$MEMORY_USAGE" ] && [ $(echo "$MEMORY_USAGE > 80" | bc) -eq 1 ]; then
    echo "$(date): High memory usage: ${MEMORY_USAGE}%" >> /var/log/internetkommunikation/monitor.log
fi
EOF

chmod +x /opt/internetkommunikation/monitor.sh

# Add to crontab
echo "*/5 * * * * /opt/internetkommunikation/monitor.sh" | crontab -
```

## 🔒 Security Configuration

### 1. User Permissions
```bash
# Create dedicated user
sudo useradd -r -s /bin/false interchat
sudo usermod -aG interchat www-data

# Set file permissions
sudo chown -R interchat:interchat /opt/internetkommunikation
sudo chmod 755 /opt/internetkommunikation
sudo chmod 644 /opt/internetkommunikation/*.py
```

### 2. Network Security
```bash
# Configure firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 65433
sudo ufw allow from 192.168.1.0/24 to any port 9999
```

### 3. Resource Limits
```bash
# Set file descriptor limits
echo "interchat soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "interchat hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

## 📊 Performance Optimization

### 1. System Tuning
```bash
# Optimize network settings
echo 'net.core.somaxconn = 65535' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Application Tuning
```python
# Performance configuration
PERFORMANCE_CONFIG = {
    'max_connections': 1000,
    'worker_threads': 4,
    'connection_timeout': 30,
    'heartbeat_interval': 60,
    'message_queue_size': 10000
}
```

## 🔄 Backup and Recovery

### 1. Backup Strategy
```bash
# Create backup script
cat > /opt/internetkommunikation/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/backup/internetkommunikation"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/internetkommunikation/config.py

# Backup log files
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /var/log/internetkommunikation/

# Backup database (if exists)
if [ -f /opt/internetkommunikation/internetkommunikation.db ]; then
    cp /opt/internetkommunikation/internetkommunikation.db $BACKUP_DIR/db_$DATE.db
fi

# Clean up old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /opt/internetkommunikation/backup.sh

# Add to crontab (backup daily at 2 AM)
echo "0 2 * * * /opt/internetkommunikation/backup.sh" | crontab -
```

### 2. Recovery Process
```bash
# Stop service
sudo systemctl stop internetkommunikation-server

# Restore configuration files
tar -xzf /backup/internetkommunikation/config_20231201_120000.tar.gz -C /

# Restore database
cp /backup/internetkommunikation/db_20231201_120000.db /opt/internetkommunikation/internetkommunikation.db

# Start service
sudo systemctl start internetkommunikation-server
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Cannot Start
```bash
# Check logs
sudo journalctl -u internetkommunikation-server -f

# Check port usage
sudo netstat -tlnp | grep :65433
sudo netstat -tlnp | grep :9999

# Check permissions
ls -la /opt/internetkommunikation/
```

#### 2. Network Connection Issues
```bash
# Check firewall
sudo ufw status

# Check network connectivity
ping -c 4 8.8.8.8

# Check port listening
sudo ss -tlnp | grep :65433
```

#### 3. Performance Issues
```bash
# Check system resources
htop
df -h
free -h

# Check process status
ps aux | grep python
```

### Debug Commands
```bash
# Real-time log viewing
tail -f /var/log/internetkommunikation/server.log

# Check service status
sudo systemctl status internetkommunikation-server

# Restart service
sudo systemctl restart internetkommunikation-server

# View system resources
top
iostat
netstat -i
```

## 📞 Technical Support

### Project Information
- **Project Repository**: [LRZ GitLab](https://gitlab.lrz.de/00000000014AEF26/internetkommunikation_project_gruppe4.git)

## 📚 Related Documentation

- [User Guide](user_guide.md)
- [Development Guide](development_guide.md)
- [API Documentation](api_documentation.md)
- [User Guide](user_guide.md) - Contains troubleshooting information 