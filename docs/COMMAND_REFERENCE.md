# Command Reference Guide

## Table of Contents

1. [Proxmox Commands](#proxmox-commands)
2. [Network Commands](#network-commands)
3. [Container Management](#container-management)
4. [PostgreSQL Commands](#postgresql-commands)
5. [Valkey Commands](#valkey-commands)
6. [NetBox Commands](#netbox-commands)
7. [Nginx Commands](#nginx-commands)
8. [Troubleshooting Commands](#troubleshooting-commands)
9. [Ansible Commands](#ansible-commands)

---

## Proxmox Commands

### System Information

```bash
# Check Proxmox version
pveversion

# View cluster status
pvecm status

# Check node resources
pvesh get /nodes/$(hostname)/status

# List all VMs and containers
qm list && pct list

# View storage status
pvesm status
```

### Kernel Parameters

```bash
# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Enable memory overcommit (required for Valkey)
sysctl -w vm.overcommit_memory=1
echo "vm.overcommit_memory=1" >> /etc/sysctl.conf

# Apply sysctl changes
sysctl -p

# View current settings
sysctl net.ipv4.ip_forward
sysctl vm.overcommit_memory
```

---

## Network Commands

### Bridge Management

```bash
# List existing bridges
brctl show

# Create bridge
brctl addbr vmbr1

# Add IP address to bridge
ip addr add 10.100.0.1/24 dev vmbr1

# Bring bridge up
ip link set vmbr1 up

# Delete bridge
ip link set vmbr1 down
brctl delbr vmbr1

# View bridge details
ip addr show vmbr1
```

### NAT/Masquerading

```bash
# Enable NAT for backend network
iptables -t nat -A POSTROUTING -s 10.100.0.0/24 -o vmbr0 -j MASQUERADE

# Enable NAT for DMZ network
iptables -t nat -A POSTROUTING -s 10.100.1.0/24 -o vmbr0 -j MASQUERADE

# List NAT rules
iptables -t nat -L -n -v

# Save iptables rules (Debian)
iptables-save > /etc/iptables/rules.v4

# Restore iptables rules
iptables-restore < /etc/iptables/rules.v4

# Delete NAT rule
iptables -t nat -D POSTROUTING -s 10.100.0.0/24 -o vmbr0 -j MASQUERADE
```

### Network Testing

```bash
# Test connectivity between containers
pct exec 100 -- ping -c 2 10.100.0.20

# Check routing table on host
ip route show

# Check routing table in container
pct exec 100 -- ip route show

# Trace route
pct exec 100 -- traceroute 10.100.0.20

# Test port connectivity
pct exec 100 -- telnet 10.100.0.20 5432
pct exec 100 -- nc -zv 10.100.0.20 5432

# DNS resolution test
pct exec 100 -- nslookup google.com
pct exec 100 -- dig google.com
```

---

## Container Management

### Template Management

```bash
# Update template list
pveam update

# List available templates
pveam available

# List available Debian templates
pveam available | grep debian

# Download template
pveam download local debian-13-standard_13.1-2_amd64.tar.zst

# List downloaded templates
pveam list local

# Remove template
pveam remove local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst
```

### Container Creation

```bash
# Create container
pct create 100 local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst \
  --hostname netbox \
  --memory 4096 \
  --swap 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr1,ip=10.100.0.10/24,gw=10.100.0.1 \
  --storage local-zfs \
  --rootfs local-zfs:32 \
  --unprivileged 1 \
  --features nesting=1 \
  --onboot 1 \
  --ostype unmanaged

# Clone container
pct clone 100 200 --hostname netbox-test

# Create container snapshot
pct snapshot 100 backup-$(date +%Y%m%d)

# List snapshots
pct listsnapshot 100

# Rollback to snapshot
pct rollback 100 backup-20251205

# Delete snapshot
pct delsnapshot 100 backup-20251205
```

### Container Control

```bash
# Start container
pct start 100

# Stop container
pct stop 100

# Restart container
pct reboot 100

# Force stop container
pct shutdown 100 --forceStop 1

# Container status
pct status 100

# List all containers
pct list

# Enter container
pct enter 100

# Execute command in container
pct exec 100 -- ls -la /

# Execute command as specific user
pct exec 100 -- su - postgres -c 'psql --version'

# Push file to container
pct push 100 /local/file.txt /container/path/file.txt

# Pull file from container
pct pull 100 /container/path/file.txt /local/file.txt
```

### Container Configuration

```bash
# View container config
pct config 100

# Set container memory
pct set 100 --memory 8192

# Set container cores
pct set 100 --cores 4

# Add network interface
pct set 100 --net1 name=eth1,bridge=vmbr2,ip=10.100.1.10/24

# Remove network interface
pct set 100 --delete net1

# Resize root filesystem
pct resize 100 rootfs +10G

# Set description
pct set 100 --description "NetBox Application Server"

# Enable/disable onboot
pct set 100 --onboot 1
pct set 100 --onboot 0
```

### Container Deletion

```bash
# Delete container (must be stopped)
pct destroy 100

# Delete container and purge all data
pct destroy 100 --purge 1

# Force delete running container
pct stop 100 && pct destroy 100
```

---

## PostgreSQL Commands

### Installation (in container)

```bash
# Update package list
pct exec 101 -- apt update

# Install PostgreSQL
pct exec 101 -- apt install -y postgresql postgresql-contrib

# Check PostgreSQL version
pct exec 101 -- psql --version
```

### Service Management

```bash
# Start PostgreSQL
pct exec 101 -- systemctl start postgresql

# Stop PostgreSQL
pct exec 101 -- systemctl stop postgresql

# Restart PostgreSQL
pct exec 101 -- systemctl restart postgresql

# Check status
pct exec 101 -- systemctl status postgresql

# Enable on boot
pct exec 101 -- systemctl enable postgresql

# View logs
pct exec 101 -- journalctl -u postgresql -f
```

### Database Operations

```bash
# Connect to PostgreSQL as postgres user
pct exec 101 -- su - postgres -c 'psql'

# Create database
pct exec 101 -- su - postgres -c "psql -c 'CREATE DATABASE netbox;'"

# Create user
pct exec 101 -- su - postgres -c "psql -c \"CREATE USER netbox WITH PASSWORD 'password';\""

# Grant privileges
pct exec 101 -- su - postgres -c "psql -c 'GRANT ALL PRIVILEGES ON DATABASE netbox TO netbox;'"

# List databases
pct exec 101 -- su - postgres -c 'psql -l'

# List users
pct exec 101 -- su - postgres -c "psql -c '\\du'"

# Connect to specific database
pct exec 101 -- su - postgres -c 'psql -d netbox'

# Execute SQL query
pct exec 101 -- su - postgres -c "psql -d netbox -c 'SELECT version();'"

# Backup database
pct exec 101 -- su - postgres -c 'pg_dump netbox' > netbox_backup_$(date +%Y%m%d).sql

# Restore database
cat netbox_backup_20251205.sql | pct exec 101 -- su - postgres -c 'psql netbox'

# Vacuum database
pct exec 101 -- su - postgres -c "psql -d netbox -c 'VACUUM ANALYZE;'"
```

### Configuration

```bash
# Edit postgresql.conf
pct exec 101 -- vim /etc/postgresql/17/main/postgresql.conf

# Edit pg_hba.conf
pct exec 101 -- vim /etc/postgresql/17/main/pg_hba.conf

# Reload configuration without restart
pct exec 101 -- su - postgres -c "psql -c 'SELECT pg_reload_conf();'"

# View configuration
pct exec 101 -- su - postgres -c "psql -c 'SHOW all;'"

# View specific setting
pct exec 101 -- su - postgres -c "psql -c 'SHOW listen_addresses;'"
```

### Monitoring

```bash
# Check connections
pct exec 101 -- su - postgres -c "psql -d netbox -c 'SELECT * FROM pg_stat_activity;'"

# Check database size
pct exec 101 -- su - postgres -c "psql -c 'SELECT pg_database_size(\\\'netbox\\\');'"

# Check table sizes
pct exec 101 -- su - postgres -c "psql -d netbox -c '\\dt+'"

# View active queries
pct exec 101 -- su - postgres -c "psql -d netbox -c 'SELECT pid, usename, query FROM pg_stat_activity WHERE state = \\\'active\\\';'"
```

---

## Valkey Commands

### Installation

```bash
# Update package list
pct exec 102 -- apt update

# Install Valkey
pct exec 102 -- apt install -y valkey-server valkey-tools

# Check version
pct exec 102 -- valkey-server --version
```

### Service Management

```bash
# Start Valkey (manual)
pct exec 102 -- valkey-server /etc/valkey/valkey.conf

# Check if Valkey is running
pct exec 102 -- ps aux | grep valkey

# Check port
pct exec 102 -- ss -tlnp | grep 6379

# Kill Valkey process
pct exec 102 -- pkill -9 valkey-server
```

### Configuration

```bash
# Edit configuration
pct exec 102 -- vim /etc/valkey/valkey.conf

# View configuration
pct exec 102 -- cat /etc/valkey/valkey.conf | grep -v '^#' | grep -v '^$'

# Test configuration
pct exec 102 -- valkey-server /etc/valkey/valkey.conf --test-memory 1024

# View logs
pct exec 102 -- tail -f /var/log/valkey/valkey-server.log
```

### Valkey CLI Operations

```bash
# Connect to Valkey
pct exec 102 -- valkey-cli

# Ping server
pct exec 102 -- valkey-cli ping

# Get server info
pct exec 102 -- valkey-cli info

# Monitor commands in real-time
pct exec 102 -- valkey-cli monitor

# Get specific info section
pct exec 102 -- valkey-cli info server
pct exec 102 -- valkey-cli info memory
pct exec 102 -- valkey-cli info stats

# Set key
pct exec 102 -- valkey-cli set mykey "myvalue"

# Get key
pct exec 102 -- valkey-cli get mykey

# List all keys
pct exec 102 -- valkey-cli keys '*'

# Flush all databases
pct exec 102 -- valkey-cli flushall

# Flush specific database
pct exec 102 -- valkey-cli -n 0 flushdb

# Get memory usage
pct exec 102 -- valkey-cli memory stats

# Save database to disk
pct exec 102 -- valkey-cli save

# Background save
pct exec 102 -- valkey-cli bgsave
```

---

## NetBox Commands

### Installation

```bash
# Install dependencies
pct exec 100 -- apt update
pct exec 100 -- apt install -y python3 python3-pip python3-venv python3-dev \
  build-essential libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev \
  zlib1g-dev git postgresql-client

# Clone NetBox repository
pct exec 100 -- git clone --depth 1 https://github.com/netbox-community/netbox.git /opt/netbox

# Create virtual environment
pct exec 100 -- python3 -m venv /opt/netbox/venv

# Install Python packages
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && pip install --upgrade pip"
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && pip install -r /opt/netbox/requirements.txt"

# Install plugins
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && pip install netbox-plugin-dns netbox-secrets"
```

### Configuration

```bash
# Copy example configuration
pct exec 100 -- cp /opt/netbox/netbox/netbox/configuration_example.py \
  /opt/netbox/netbox/netbox/configuration.py

# Edit configuration
pct exec 100 -- vim /opt/netbox/netbox/netbox/configuration.py

# Generate secret key
pct exec 100 -- python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Validate configuration
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py check"
```

### Database Operations

```bash
# Run migrations
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py migrate"

# Create superuser
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py createsuperuser"

# Change user password
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py changepassword admin"

# Collect static files
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py collectstatic --noinput"

# Clear cache
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py clearcache"

# List installed plugins
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py showmigrations"
```

### Service Management

```bash
# Start NetBox with Gunicorn (manual)
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && gunicorn --bind 10.100.1.10:8000 --workers 4 netbox.wsgi &"

# Start NetBox service (systemd)
pct exec 100 -- systemctl start netbox

# Stop NetBox service
pct exec 100 -- systemctl stop netbox

# Restart NetBox service
pct exec 100 -- systemctl restart netbox

# Check service status
pct exec 100 -- systemctl status netbox

# Enable on boot
pct exec 100 -- systemctl enable netbox

# View logs
pct exec 100 -- journalctl -u netbox -f

# Check Gunicorn processes
pct exec 100 -- ps aux | grep gunicorn

# Check listening ports
pct exec 100 -- ss -tlnp | grep 8000
```

### Troubleshooting

```bash
# Run development server (for testing)
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py runserver 0.0.0.0:8000"

# Test database connectivity
pct exec 100 -- bash -c "PGPASSWORD='password' psql -h 10.100.0.20 -U netbox -d netbox -c 'SELECT 1;'"

# Test Valkey connectivity
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && python3 -c \
  'import redis; r = redis.Redis(host=\"10.100.0.30\"); print(r.ping())'"

# Django shell
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py shell"

# Show NetBox version
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py version"
```

### Updates

```bash
# Backup before update
pct exec 101 -- su - postgres -c 'pg_dump netbox' > netbox_pre_update_$(date +%Y%m%d).sql

# Pull latest code
pct exec 100 -- bash -c "cd /opt/netbox && git pull"

# Update dependencies
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  pip install --upgrade -r /opt/netbox/requirements.txt"

# Run migrations
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py migrate"

# Collect static files
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py collectstatic --noinput"

# Restart service
pct exec 100 -- systemctl restart netbox
```

---

## Nginx Commands

### Installation

```bash
# Install Nginx
pct exec 103 -- apt update
pct exec 103 -- apt install -y nginx

# Check version
pct exec 103 -- nginx -v
```

### Service Management

```bash
# Start Nginx
pct exec 103 -- systemctl start nginx

# Stop Nginx
pct exec 103 -- systemctl stop nginx

# Restart Nginx
pct exec 103 -- systemctl restart nginx

# Reload configuration
pct exec 103 -- systemctl reload nginx

# Check status
pct exec 103 -- systemctl status nginx

# Enable on boot
pct exec 103 -- systemctl enable nginx

# Test configuration
pct exec 103 -- nginx -t

# View error log
pct exec 103 -- tail -f /var/log/nginx/error.log

# View access log
pct exec 103 -- tail -f /var/log/nginx/access.log
```

### SSL Certificate Management

```bash
# Generate self-signed certificate
pct exec 103 -- mkdir -p /etc/nginx/ssl
pct exec 103 -- openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout /etc/nginx/ssl/netbox.key \
  -out /etc/nginx/ssl/netbox.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=netbox.local"

# Generate CSR for CA-signed certificate
pct exec 103 -- openssl req -new -newkey rsa:4096 -nodes \
  -keyout /etc/nginx/ssl/netbox.key \
  -out /etc/nginx/ssl/netbox.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=netbox.local"

# View certificate details
pct exec 103 -- openssl x509 -in /etc/nginx/ssl/netbox.crt -text -noout

# Verify certificate and key match
pct exec 103 -- bash -c "openssl x509 -noout -modulus -in /etc/nginx/ssl/netbox.crt | openssl md5; \
  openssl rsa -noout -modulus -in /etc/nginx/ssl/netbox.key | openssl md5"

# Test SSL configuration
pct exec 103 -- openssl s_client -connect localhost:443
```

### Configuration

```bash
# Edit main configuration
pct exec 103 -- vim /etc/nginx/nginx.conf

# Create site configuration
pct exec 103 -- vim /etc/nginx/sites-available/netbox

# Enable site
pct exec 103 -- ln -s /etc/nginx/sites-available/netbox /etc/nginx/sites-enabled/

# Disable default site
pct exec 103 -- rm /etc/nginx/sites-enabled/default

# Test configuration syntax
pct exec 103 -- nginx -t

# View configuration structure
pct exec 103 -- nginx -T
```

---

## Troubleshooting Commands

### Network Diagnostics

```bash
# Test connectivity
pct exec 100 -- ping -c 4 10.100.0.20

# Test port
pct exec 100 -- nc -zv 10.100.0.20 5432
pct exec 100 -- telnet 10.100.0.20 5432

# Check DNS resolution
pct exec 100 -- nslookup google.com
pct exec 100 -- dig google.com

# Trace route
pct exec 100 -- traceroute 10.100.0.20
pct exec 100 -- mtr 10.100.0.20

# Check open ports
pct exec 100 -- ss -tulpn
pct exec 100 -- netstat -tulpn

# View routing table
pct exec 100 -- ip route show

# View network interfaces
pct exec 100 -- ip addr show
```

### Container Diagnostics

```bash
# Check container logs
pct exec 100 -- journalctl -xe

# Check system log
pct exec 100 -- tail -100 /var/log/syslog

# Check resource usage
pct exec 100 -- top
pct exec 100 -- htop

# Check disk usage
pct exec 100 -- df -h
pct exec 100 -- du -sh /opt/netbox

# Check memory usage
pct exec 100 -- free -h

# Check running processes
pct exec 100 -- ps aux

# Check container from host
pct status 100
pct config 100
```

### Application Diagnostics

```bash
# Check NetBox logs
pct exec 100 -- journalctl -u netbox -n 100

# Check Gunicorn processes
pct exec 100 -- ps aux | grep gunicorn

# Check database connection
pct exec 100 -- bash -c "PGPASSWORD='password' psql -h 10.100.0.20 -U netbox -d netbox -c 'SELECT 1;'"

# Check cache connection
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && python3 -c \
  'import redis; r = redis.Redis(host=\"10.100.0.30\"); print(r.ping())'"

# Test NetBox web interface
curl -k https://localhost

# Check SSL certificate
openssl s_client -connect localhost:443 -showcerts
```

### Performance Monitoring

```bash
# Monitor system resources (host)
htop
vmstat 1
iostat -x 1

# Monitor container resources
pct exec 100 -- top -b -n 1

# Monitor network traffic
iftop -i vmbr0
tcpdump -i vmbr1 -n port 5432

# Monitor PostgreSQL
pct exec 101 -- su - postgres -c "psql -d netbox -c \
  'SELECT * FROM pg_stat_activity;'"

# Monitor Valkey
pct exec 102 -- valkey-cli --stat
pct exec 102 -- valkey-cli monitor
```

---

## Ansible Commands

### Setup

```bash
# Install Ansible
apt install -y ansible

# Install Proxmox collection
ansible-galaxy collection install community.general

# Install requirements
ansible-galaxy install -r requirements.yml

# Create vault password file
echo "your-vault-password" > ~/.vault_pass
chmod 600 ~/.vault_pass
```

### Inventory Management

```bash
# List hosts
ansible-inventory -i inventory/production --list

# View host variables
ansible-inventory -i inventory/production --host ct100

# Graph inventory
ansible-inventory -i inventory/production --graph

# Test connectivity
ansible all -i inventory/production -m ping
```

### Vault Operations

```bash
# Create encrypted file
ansible-vault create group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# Encrypt existing file
ansible-vault encrypt group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# Decrypt file
ansible-vault decrypt group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# Edit encrypted file
ansible-vault edit group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# View encrypted file
ansible-vault view group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# Rekey (change password)
ansible-vault rekey group_vars/all/vault.yml --vault-password-file ~/.vault_pass
```

### Playbook Execution

```bash
# Run full deployment
ansible-playbook site.yml --vault-password-file ~/.vault_pass

# Check mode (dry run)
ansible-playbook site.yml --check

# Diff mode (show changes)
ansible-playbook site.yml --check --diff

# Run specific tags
ansible-playbook site.yml --tags "network,database"

# Skip specific tags
ansible-playbook site.yml --skip-tags "proxy"

# Limit to specific hosts
ansible-playbook site.yml --limit ct100

# Start at specific task
ansible-playbook site.yml --start-at-task "Install PostgreSQL"

# Verbose output
ansible-playbook site.yml -v
ansible-playbook site.yml -vv
ansible-playbook site.yml -vvv

# Extra variables
ansible-playbook site.yml -e "netbox_version=v3.7.0"
ansible-playbook site.yml -e "force=yes"
```

### Testing

```bash
# Lint playbooks
ansible-lint playbooks/

# Lint specific playbook
ansible-lint playbooks/site.yml

# Syntax check
ansible-playbook site.yml --syntax-check

# Test role with Molecule
cd roles/postgresql
molecule test

# Run specific Molecule scenario
molecule test -s centos8
```

### Ad-hoc Commands

```bash
# Execute command on all hosts
ansible all -i inventory/production -a "uptime"

# Execute with sudo
ansible all -i inventory/production -a "systemctl status nginx" -b

# Copy file
ansible all -i inventory/production -m copy -a "src=/tmp/file dest=/tmp/file"

# Install package
ansible all -i inventory/production -m apt -a "name=htop state=present" -b

# Restart service
ansible all -i inventory/production -m systemd -a "name=nginx state=restarted" -b

# Gather facts
ansible all -i inventory/production -m setup
```

---

## Quick Reference Scripts

### Complete Deployment Script

```bash
#!/bin/bash
# deploy-netbox.sh

set -euo pipefail

VAULT_PASS=~/.vault_pass

echo "=== Starting NetBox Deployment ==="

echo "1. Checking prerequisites..."
ansible --version
pveversion | grep 'pve-manager/9'

echo "2. Running deployment playbook..."
ansible-playbook site.yml \
  --vault-password-file "$VAULT_PASS" \
  -v

echo "3. Verifying deployment..."
ansible-playbook playbooks/verify.yml

echo "=== Deployment Complete ==="
echo "NetBox URL: https://$(pct exec 103 -- ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1)"
echo "Username: admin"
echo "Password: See vault.yml"
```

### Backup Script

```bash
#!/bin/bash
# backup-netbox.sh

BACKUP_DIR=/root/netbox-backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Backing up NetBox database..."
pct exec 101 -- su - postgres -c 'pg_dump netbox' > "$BACKUP_DIR/netbox-db-$DATE.sql"

echo "Backing up NetBox configuration..."
pct pull 100 /opt/netbox/netbox/netbox/configuration.py "$BACKUP_DIR/configuration-$DATE.py"

echo "Creating container snapshots..."
for ct in 100 101 102 103; do
  pct snapshot $ct backup-$DATE
done

echo "Backup complete: $BACKUP_DIR"
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

echo "=== NetBox Health Check ==="

echo "1. Container Status:"
pct list

echo -e "\n2. Service Status:"
pct exec 100 -- systemctl is-active netbox
pct exec 101 -- systemctl is-active postgresql
pct exec 103 -- systemctl is-active nginx

echo -e "\n3. Network Connectivity:"
pct exec 100 -- ping -c 1 10.100.0.20 > /dev/null && echo "DB: OK" || echo "DB: FAIL"
pct exec 100 -- ping -c 1 10.100.0.30 > /dev/null && echo "Cache: OK" || echo "Cache: FAIL"

echo -e "\n4. Port Checks:"
pct exec 100 -- nc -zv 10.100.0.20 5432 2>&1 | grep succeeded
pct exec 100 -- nc -zv 10.100.0.30 6379 2>&1 | grep succeeded

echo -e "\n5. Web Interface:"
curl -k -s -o /dev/null -w "%{http_code}" https://localhost

echo -e "\n=== Health Check Complete ==="
```

---

## Environment Variables

### Useful Environment Variables

```bash
# Set in ~/.bashrc or ~/.profile

# Ansible
export ANSIBLE_CONFIG=~/netbox-proxmox-ansible/ansible.cfg
export ANSIBLE_INVENTORY=~/netbox-proxmox-ansible/inventory/production
export ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass

# Proxmox
export PVE_NODE=$(hostname)

# Container shortcuts
alias nb-shell='pct enter 100'
alias db-shell='pct enter 101'
alias cache-shell='pct enter 102'
alias proxy-shell='pct enter 103'
```

---

This command reference provides the essential commands used throughout the NetBox deployment on Proxmox VE 9.0. For more detailed information, refer to the ARCHITECTURE.md and ANSIBLE_DESIGN.md documentation.
