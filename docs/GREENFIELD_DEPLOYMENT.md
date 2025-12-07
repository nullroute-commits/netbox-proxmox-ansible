# Greenfield Deployment Guide

## Overview

Complete automated deployment of NetBox on Proxmox VE 9.1 from a clean environment. This guide ensures successful deployment on a greenfield Proxmox installation with proper hardware and software prerequisites.

## Hardware and Software Capabilities

**Important:** For comprehensive hardware specifications, system requirements, and deployment configurations, refer to the **[automation_nation.git](https://github.com/nullroute-commits/automation_nation.git)** project. This companion repository provides:

- **Hardware Compatibility Matrices**: Validated hardware configurations for Proxmox deployments
- **Performance Benchmarks**: Expected performance metrics for various hardware profiles
- **Capacity Planning**: Tools to calculate resource requirements for your specific use case
- **Node Configuration Templates**: Pre-validated hardware and software configurations
- **Deployment Best Practices**: Production-tested deployment patterns and recommendations

## Prerequisites

### Proxmox VE Requirements

**Version Requirements:**
- Proxmox VE 9.1+ (tested on 9.1.0)
- Backward compatible with Proxmox VE 9.0.x
- Kernel 6.14+ recommended

**Installation State:**
- Fresh Proxmox VE installation or existing cluster node
- Accessible via SSH with root privileges
- Internet connectivity established
- Time synchronization configured (NTP)

### Hardware Requirements

Refer to [automation_nation.git](https://github.com/nullroute-commits/automation_nation.git) for detailed specifications. Minimum requirements:

**Compute:**
- CPU: Dual-core processor (quad-core recommended)
- CPU Features: VT-x/AMD-V enabled for nested virtualization
- Architecture: x86_64 (amd64)

**Memory:**
- Minimum: 8GB RAM (4GB for Proxmox + 8GB for containers)
- Recommended: 16GB RAM for production workloads
- Swap: At least 4GB swap space on Proxmox host

**Storage:**
- Minimum: 100GB available storage
- Recommended: 200GB+ for production with backups
- Filesystem: ZFS recommended, ext4 minimum
- IOPS: SSD recommended for PostgreSQL performance

**Network:**
- Network interface(s) connected and configured
- DHCP or static IP configuration
- Internet access for package downloads
- DNS resolution working

### Network Requirements

**Bridge Configuration:**
- `vmbr0`: External/physical bridge (must exist or be created)
- `vmbr1`: Backend network bridge (will be created)
- `vmbr2`: DMZ network bridge (will be created)

**Connectivity:**
- Outbound HTTPS (443) for package repositories
- Outbound HTTP (80) for Debian mirrors
- DNS resolution to public servers
- No incoming firewall restrictions required

### Software Prerequisites

**On Control Node (where Ansible runs):**
- Ansible 2.14+ installed (2.17+ recommended)
- Python 3.10+ 
- SSH client configured
- Git (for repository cloning)

**On Proxmox Host:**
- Proxmox VE 9.1+ installed
- Standard Proxmox repositories enabled
- Root SSH access configured
- No conflicting container VMIDs (100-103)

## Pre-Deployment Checklist

Before starting deployment, verify:

- [ ] Proxmox VE 9.1+ is installed and accessible
- [ ] Root SSH access to Proxmox host is configured
- [ ] Internet connectivity is available from Proxmox host
- [ ] At least 8GB RAM is free (check with `free -h`)
- [ ] At least 100GB storage is available (check with `df -h`)
- [ ] No existing containers with VMIDs 100-103 (check with `pct list`)
- [ ] No existing bridges vmbr1 or vmbr2 (check with `brctl show`)
- [ ] Ansible 2.14+ is installed on control node
- [ ] Hardware meets minimum requirements (see automation_nation.git)
- [ ] Network configuration allows outbound connectivity

## Prerequisites Validation

Run these commands on the Proxmox host to validate prerequisites:

```bash
# Check Proxmox version
pveversion

# Check available resources
free -h
df -h /var/lib/vz

# Check existing containers
pct list

# Check existing bridges
brctl show

# Check internet connectivity
ping -c 2 debian.org

# Check DNS resolution
nslookup github.com
```

Expected results:
- Proxmox VE 9.1 or later
- At least 8GB free RAM
- At least 100GB free in /var/lib/vz
- No containers with VMIDs 100-103
- Only vmbr0 exists (vmbr1, vmbr2 should not exist yet)
- Successful ping to debian.org
- Successful DNS resolution

## Prerequisites

- Proxmox VE 9.1+ installed and accessible
- Ansible 2.14+ installed on control node
- Internet connectivity from Proxmox host
- At least 8GB RAM available (16GB recommended)
- At least 50GB disk space (100GB recommended)
- Hardware validated using automation_nation.git specifications

### Ansible Control Node Requirements

**Operating System:**
- Linux (Ubuntu 22.04+, Debian 12+, RHEL 9+, etc.)
- macOS 12+ (with Homebrew)
- WSL2 on Windows (Ubuntu distribution)

**Software:**
- Python 3.10 or later (`python3 --version`)
- pip (Python package manager)
- Git (`git --version`)
- SSH client with key-based authentication configured

**Installation:**
```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip git openssh-client

# Install Ansible
pip3 install ansible-core>=2.17.0

# Verify installation
ansible --version
```

## Quick Start

### 1. Prepare Environment

```bash
# Clone repository
git clone https://github.com/nullroute-commits/netbox-proxmox-ansible.git
cd netbox-proxmox-ansible

# Validate prerequisites on Proxmox host
./scripts/validate-prerequisites.sh

# If validation passes, continue with setup
# Install Ansible collections
ansible-galaxy collection install -r requirements.yml

# Create vault password file
echo "netbox-deployment-2025" > .vault_pass
chmod 600 .vault_pass
```

### 2. Review Configuration

Check and customize if needed:

```bash
# Network configuration
cat group_vars/all/network.yml

# Container specifications
cat group_vars/all/containers.yml

# Software versions
cat group_vars/all/versions.yml

# Secrets (encrypted)
ansible-vault view group_vars/all/vault.yml --vault-password-file .vault_pass
```

### 3. Deploy

#### Option A: Full Automated Deployment (Recommended)

```bash
ansible-playbook playbooks/greenfield-deployment.yml --vault-password-file .vault_pass
```

**Estimated time:** 30-45 minutes

**What it does:**
1. ✅ Configures Proxmox host (sysctl, packages)
2. ✅ Creates network bridges (vmbr1, vmbr2)
3. ✅ Configures NAT/masquerading
4. ✅ Creates 4 LXC containers
5. ✅ Installs and configures PostgreSQL 17.6
6. ✅ Installs and configures Valkey 8.1.1
7. ✅ Installs NetBox v4.4.7 with 7 plugins
8. ✅ Configures Nginx reverse proxy with SSL
9. ✅ Verifies all services

#### Option B: Infrastructure Only

```bash
ansible-playbook playbooks/deploy-infrastructure.yml --vault-password-file .vault_pass
```

Then follow manual deployment in `DEPLOYMENT_COMPLETE.md`.

### 4. Verify Deployment

```bash
# Run verification playbook
ansible-playbook playbooks/verify-deployment.yml --vault-password-file .vault_pass

# Check container status
pct list

# Check services
pct exec 100 -- systemctl status netbox
pct exec 101 -- systemctl status postgresql
pct exec 102 -- systemctl status valkey
pct exec 103 -- systemctl status nginx
```

### 5. Access NetBox

```bash
# Get proxy IP
pct exec 103 -- ip -4 addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1

# Access via browser
https://<proxy-ip>

# Default credentials
Username: admin
Password: NetBox2024!
```

## Deployment Phases

The greenfield deployment runs in 7 phases:

### Phase 1: Infrastructure Setup
- Install required packages
- Configure sysctl parameters
- Create network bridges (vmbr1, vmbr2)
- Configure NAT rules
- Download Debian template

### Phase 2: Container Creation
- Create database container (CT 101)
- Create cache container (CT 102)
- Create application container (CT 100)
- Create proxy container (CT 103)
- Configure network interfaces

### Phase 3: Database Configuration
- Install Debian base packages
- Install PostgreSQL 17.6
- Configure network access
- Create NetBox database and user
- Grant privileges

### Phase 4: Cache Configuration
- Install Debian base packages
- Add Valkey repository
- Install Valkey 8.1.1
- Configure network binding
- Start Valkey service

### Phase 5: NetBox Application
- Install Python 3.13 and dependencies
- Clone NetBox v4.4.7
- Create virtual environment
- Install NetBox requirements
- Install 7 plugins
- Configure database/cache connections
- Run migrations
- Create superuser
- Start NetBox service

### Phase 6: Nginx Proxy
- Install Nginx 1.26.3
- Generate self-signed SSL certificate
- Configure reverse proxy
- Enable HTTPS
- Start Nginx service

### Phase 7: Verification
- Check all service statuses
- Test database connectivity
- Test cache connectivity
- Test HTTPS endpoint
- Display deployment summary

## Network Architecture

```
Internet
   ↓
vmbr0 (External)
   ↓
CT 103 (Nginx Proxy)
   ↓ eth1
vmbr2 (DMZ 10.100.1.0/24)
   ↓ eth1
CT 100 (NetBox App)
   ↓ eth0
vmbr1 (Backend 10.100.0.0/24)
   ├─→ CT 101 (PostgreSQL)
   └─→ CT 102 (Valkey)
```

## Container Specifications

| Container | VMID | vCPU | RAM | Disk | IP (Backend) | IP (DMZ) |
|-----------|------|------|-----|------|--------------|----------|
| netbox-db | 101 | 2 | 2GB | 10GB | 10.100.0.20 | - |
| netbox-redis | 102 | 1 | 1GB | 8GB | 10.100.0.30 | - |
| netbox | 100 | 2 | 4GB | 20GB | 10.100.0.10 | 10.100.1.10 |
| netbox-proxy | 103 | 1 | 512MB | 8GB | - | 10.100.1.40 |

## Software Versions

All versions pinned to stable releases (December 2025):

- **Proxmox VE:** 9.0.3
- **Debian:** 13.1 (Trixie)
- **NetBox:** v4.4.7
- **PostgreSQL:** 17.6 (EOL: Nov 2029)
- **Valkey:** 8.1.1
- **Python:** 3.13.5 (EOL: Oct 2029)
- **Nginx:** 1.26.3
- **Gunicorn:** 23.0.0

See [VERSIONS.md](../VERSIONS.md) for complete version details.

## Plugins Installed

1. **netbox-plugin-dns** (1.4.4) - DNS management
2. **netbox-secrets** (2.4.1) - Secret storage
3. **netbox-acls** (1.9.1) - Access control lists
4. **netbox-bgp** (0.17.0) - BGP peering
5. **netbox-inventory** (2.4.1) - Inventory tracking
6. **netbox-floorplan-plugin** (0.8.0) - Floor planning
7. **netbox-reorder-rack** (1.1.4) - Rack reordering

## Troubleshooting

### Deployment Fails at Network Phase

```bash
# Check bridges
brctl show

# Recreate bridges manually
brctl addbr vmbr1
ip addr add 10.100.0.1/24 dev vmbr1
ip link set vmbr1 up
```

### Container Creation Fails

```bash
# Check template
ls -lh /var/lib/vz/template/cache/

# Download manually
pveam download local debian-13-standard_13.1-2_amd64.tar.zst
```

### Service Won't Start

```bash
# Check logs
pct exec <vmid> -- journalctl -u <service> -n 50

# Check network
pct exec <vmid> -- ip addr
pct exec <vmid> -- ping -c 2 8.8.8.8
```

### Database Connection Fails

```bash
# Test from NetBox container
pct exec 100 -- bash -c "PGPASSWORD='NetBox123!' psql -h 10.100.0.20 -U netbox -d netbox -c 'SELECT 1;'"

# Check PostgreSQL logs
pct exec 101 -- tail -f /var/log/postgresql/postgresql-17-main.log
```

## Customization

### Change IP Addresses

Edit `group_vars/all/network.yml`:

```yaml
backend_network:
  name: "vmbr1"
  cidr: "10.100.0.0/24"
  gateway: "10.100.0.1"

dmz_network:
  name: "vmbr2"
  cidr: "10.100.1.0/24"
  gateway: "10.100.1.1"
```

### Change Container Resources

Edit `group_vars/all/containers.yml`:

```yaml
containers:
  application:
    cpu: 4        # Increase vCPU
    memory: 8192  # Increase RAM to 8GB
```

### Change Passwords

```bash
# Edit vault
ansible-vault edit group_vars/all/vault.yml --vault-password-file .vault_pass

# Change:
# - vault_netbox_db_password
# - vault_netbox_admin_password
# - vault_container_root_password
```

## Post-Deployment

### Change Admin Password

```bash
pct exec 100 -- sudo -u netbox /opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py changepassword admin
```

### Install Production SSL Certificate

```bash
# Install certbot
pct exec 103 -- apt install -y certbot python3-certbot-nginx

# Obtain certificate (requires public DNS)
pct exec 103 -- certbot --nginx -d yourdomain.com
```

### Create Snapshots

```bash
# Create snapshots of all containers
for ct in 100 101 102 103; do
  pct snapshot $ct deployment-$(date +%Y%m%d)
done
```

### Setup Backups

```bash
# Add to crontab
0 2 * * * vzdump 100 --mode snapshot --storage backup-storage
0 2 * * * vzdump 101 --mode snapshot --storage backup-storage
0 2 * * * vzdump 102 --mode snapshot --storage backup-storage
0 2 * * * vzdump 103 --mode snapshot --storage backup-storage
```

## Roles Implemented

All 8 roles are fully implemented for greenfield deployment:

✅ **proxmox_host** - Host preparation
✅ **proxmox_network** - Network configuration
✅ **proxmox_container** - Container creation
✅ **debian_base** - Base system configuration
✅ **postgresql** - Database installation
✅ **valkey** - Cache installation
✅ **netbox_app** - NetBox installation
✅ **nginx_proxy** - Reverse proxy configuration

## Support

- **Documentation:** See `docs/` directory
- **Issues:** https://github.com/nullroute-commits/netbox-proxmox-ansible/issues
- **Verification:** Run `playbooks/verify-deployment.yml`

## License

MIT License - See [LICENSE](../LICENSE) file

---

**Status:** ✅ Production Ready  
**Last Updated:** December 5, 2025  
**Deployment Time:** 30-45 minutes (automated)
