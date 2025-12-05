# NetBox on Proxmox VE 9.0 - Ansible Automation

Automated deployment of NetBox IPAM/DCIM application on Proxmox VE 9.0 using LXC containers with three-tier network architecture.

## Features

- ✅ **Three-Tier Network Security**: External, DMZ, and Backend network isolation
- ✅ **Containerized Architecture**: Separate containers for app, database, cache, and proxy
- ✅ **Latest Technology Stack**: NetBox (latest), PostgreSQL 17, Valkey 8.1, Nginx
- ✅ **Full Plugin Support**: DNS, Secrets, ACLs, BGP, Inventory, Floorplan, Rack Reordering
- ✅ **Infrastructure as Code**: Complete Ansible automation
- ✅ **Production Ready**: Systemd services, logging, monitoring hooks
- ✅ **Security Hardened**: Unprivileged containers, network segmentation, SSL/TLS

## Quick Start

```bash
# 1. Clone repository
git clone <repo-url> /root/netbox-proxmox-ansible
cd /root/netbox-proxmox-ansible

# 2. Install Ansible
apt install -y ansible

# 3. Configure inventory
cp inventory/production/hosts.yml.example inventory/production/hosts.yml
vim inventory/production/hosts.yml

# 4. Configure variables
cp group_vars/all/vault.yml.example group_vars/all/vault.yml
vim group_vars/all/vault.yml

# 5. Encrypt secrets
ansible-vault encrypt group_vars/all/vault.yml

# 6. Run deployment
ansible-playbook site.yml --ask-vault-pass

# 7. Access NetBox
# Navigate to: https://<proxy-ip>/
# Username: admin
# Password: (from vault.yml)
```

## Architecture Overview

```
External Network (vmbr0) ─────┬───── CT 103 (Nginx Proxy)
                               │           │
DMZ Network (vmbr2)           │      ┌────┴────┐
10.100.1.0/24  ───────────────┼──────┤ CT 100  │
                               │      │ NetBox  │
                               │      └────┬────┘
Backend Network (vmbr1)       │           │
10.100.0.0/24  ───────────────┴────┬──────┴──────┬─────
                                    │             │
                              ┌─────┴──────┐ ┌───┴────┐
                              │ CT 101     │ │ CT 102 │
                              │ PostgreSQL │ │ Valkey │
                              └────────────┘ └────────┘
```

## Container Layout

| Container | VMID | Purpose | CPUs | RAM | IPs |
|-----------|------|---------|------|-----|-----|
| netbox | 100 | Application | 2 | 4GB | 10.100.0.10, 10.100.1.10 |
| netbox-db | 101 | PostgreSQL | 2 | 2GB | 10.100.0.20 |
| netbox-redis | 102 | Valkey Cache | 1 | 1GB | 10.100.0.30 |
| netbox-proxy | 103 | Nginx Proxy | 1 | 512MB | DHCP, 10.100.1.40 |

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Proxmox VE | 9.0 | Virtualization Platform |
| Debian | 13 (Trixie) | Container OS |
| NetBox | Latest (main) | IPAM/DCIM Application |
| PostgreSQL | 17.6 | Database |
| Valkey | 8.1.1 | Cache & Task Queue |
| Gunicorn | 23.0.0 | WSGI Server |
| Nginx | Latest | Reverse Proxy |
| Python | 3.13 | Runtime |

## NetBox Plugins

All plugins at latest compatible versions:

1. **netbox-dns** - DNS zone/record management
2. **netbox-secrets** - Encrypted secret storage
3. **netbox-acls** - Access control lists
4. **netbox-bgp** - BGP peering management
5. **netbox-inventory** - Enhanced inventory
6. **netbox-floorplan** - Datacenter floor plans
7. **netbox-reorder-rack** - Rack device reordering

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture, design decisions, and operational procedures
- **[ANSIBLE_DESIGN.md](docs/ANSIBLE_DESIGN.md)** - Ansible project structure, roles, and automation design
- **[COMMAND_REFERENCE.md](docs/COMMAND_REFERENCE.md)** - Complete command reference for all components

## Prerequisites

- Proxmox VE 9.0 installed and configured
- At least 8GB RAM available for containers
- 100GB storage (ZFS recommended)
- Internet connectivity for package downloads
- Root or sudo access to Proxmox host

## Installation Steps

### 1. Prepare Proxmox Host

```bash
# Install required packages
apt update
apt install -y ansible git bridge-utils python3-proxmoxer

# Enable IP forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

### 2. Clone and Configure

```bash
# Clone repository
git clone <repo-url> /root/netbox-proxmox-ansible
cd /root/netbox-proxmox-ansible

# Install Ansible dependencies
ansible-galaxy collection install -r requirements.yml
```

### 3. Configure Variables

Edit inventory and variables:

```bash
# Configure inventory
vim inventory/production/hosts.yml

# Set global variables
vim inventory/production/group_vars/all.yml

# Set network configuration
vim group_vars/all/network.yml

# Set container specifications
vim group_vars/all/containers.yml

# Configure secrets (then encrypt)
vim group_vars/all/vault.yml
ansible-vault encrypt group_vars/all/vault.yml
```

### 4. Deploy

```bash
# Full deployment
ansible-playbook site.yml --ask-vault-pass

# Or step-by-step
ansible-playbook playbooks/01-proxmox-setup.yml
ansible-playbook playbooks/02-network-setup.yml
ansible-playbook playbooks/03-containers-create.yml
ansible-playbook playbooks/04-database-setup.yml
ansible-playbook playbooks/05-cache-setup.yml
ansible-playbook playbooks/06-netbox-setup.yml
ansible-playbook playbooks/07-proxy-setup.yml
```

### 5. Verify

```bash
# Check container status
pct list

# Verify services
pct exec 100 -- systemctl status netbox
pct exec 101 -- systemctl status postgresql
pct exec 103 -- systemctl status nginx

# Access web interface
curl -k https://<proxy-ip>/
```

## Post-Installation

### Update Admin Password

```bash
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py changepassword admin"
```

### Configure SSL Certificate

```bash
# Copy your certificate
pct push 103 /path/to/cert.crt /etc/nginx/ssl/netbox.crt
pct push 103 /path/to/cert.key /etc/nginx/ssl/netbox.key

# Reload Nginx
pct exec 103 -- systemctl reload nginx
```

### Enable Backups

```bash
# Setup daily database backups
pct exec 101 -- bash -c 'echo "0 2 * * * postgres pg_dump netbox > /var/backups/netbox_\$(date +\%Y\%m\%d).sql" | crontab -'

# Create container snapshots
for ct in 100 101 102 103; do
  pct snapshot $ct weekly-$(date +%Y%m%d)
done
```

## Maintenance

### Update NetBox

```bash
# Backup database first
pct exec 101 -- su - postgres -c 'pg_dump netbox' > netbox_pre_update.sql

# Update code
pct exec 100 -- bash -c "cd /opt/netbox && git pull"

# Update dependencies
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  pip install -U -r /opt/netbox/requirements.txt"

# Run migrations
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py migrate"

# Restart
pct exec 100 -- systemctl restart netbox
```

### System Updates

```bash
# Update all containers
for ct in 100 101 102 103; do
  pct exec $ct -- apt update
  pct exec $ct -- apt upgrade -y
done

# Reboot if needed
for ct in 100 101 102 103; do
  pct reboot $ct
done
```

## Troubleshooting

### Container Won't Start

```bash
# Check container status
pct status 100

# View container log
pct exec 100 -- journalctl -xe

# Check network interfaces
pct exec 100 -- ip addr show
```

### Database Connection Issues

```bash
# Test connectivity
pct exec 100 -- ping 10.100.0.20

# Test database
pct exec 100 -- psql -h 10.100.0.20 -U netbox -d netbox -c 'SELECT 1;'

# Check PostgreSQL logs
pct exec 101 -- tail -f /var/log/postgresql/postgresql-17-main.log
```

### Web Interface Not Accessible

```bash
# Check NetBox service
pct exec 100 -- systemctl status netbox

# Check Nginx
pct exec 103 -- systemctl status nginx

# Check logs
pct exec 100 -- journalctl -u netbox -f
pct exec 103 -- tail -f /var/log/nginx/error.log
```

### Performance Issues

```bash
# Check container resources
pct exec 100 -- top

# Check database connections
pct exec 101 -- su - postgres -c "psql -d netbox -c 'SELECT * FROM pg_stat_activity;'"

# Check cache
pct exec 102 -- valkey-cli info stats
```

## Security Considerations

- Change default passwords immediately
- Use Let's Encrypt for production SSL certificates
- Implement firewall rules on Proxmox host
- Regular security updates
- Monitor logs for suspicious activity
- Backup encryption keys and certificates

## High Availability (Future)

To extend this deployment for HA:

1. **Proxmox Cluster**: Add 2+ nodes
2. **Database Replication**: PostgreSQL streaming replication + Patroni
3. **Application Scaling**: Multiple NetBox containers + HAProxy
4. **Cache Redundancy**: Valkey Sentinel or Cluster
5. **Shared Storage**: Ceph RBD for persistent data

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## Badges

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Ansible](https://img.shields.io/badge/ansible-%3E%3D2.14-blue.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Proxmox](https://img.shields.io/badge/proxmox-9.0-orange.svg)
![NetBox](https://img.shields.io/badge/netbox-latest-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

MIT License is chosen for maximum compatibility with:
- NetBox (Apache 2.0)
- Ansible (GPL 3.0)
- PostgreSQL (PostgreSQL License)
- Nginx (BSD-2-Clause)

## Support

- Documentation: `docs/` directory
- Issues: [GitHub Issues]
- Community: [Discord/Slack/Forum]

## Acknowledgments

- NetBox Community
- Proxmox Team
- Debian Project
- Ansible Contributors

---

**Project Status**: Production Ready ✅

**Last Updated**: December 2025

**Tested On**: Proxmox VE 9.0, Debian 13 (Trixie)
