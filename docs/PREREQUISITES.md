# Prerequisites for NetBox Deployment on Proxmox VE 9.1

This document provides comprehensive prerequisites for deploying NetBox on Proxmox VE 9.1+ using this Ansible automation framework.

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Network Requirements](#network-requirements)
- [Proxmox Host Requirements](#proxmox-host-requirements)
- [Control Node Requirements](#control-node-requirements)
- [Pre-Deployment Validation](#pre-deployment-validation)

## Hardware Requirements

### Reference Hardware Specifications

Before deployment, use the **[automation_nation.git](https://github.com/nullroute-commits/automation_nation.git)** bash script to collect comprehensive hardware and software information from your Proxmox node:

```bash
# On Proxmox host
git clone https://github.com/nullroute-commits/automation_nation.git
cd automation_nation

# Collect comprehensive system information
./collect_info.sh -o proxmox_node_capabilities.json

# Review the JSON output for:
# - CPU architecture and virtualization support
# - Memory and swap configuration  
# - Storage devices and capacity
# - Network interfaces
# - Installed packages and versions
# - Kernel and OS information
```

This JSON output provides a complete inventory of your node's capabilities, helping validate prerequisites before deployment.

### Minimum Hardware Requirements

**CPU:**
- Architecture: x86_64 (AMD64)
- Cores: 2 physical cores minimum (4 cores recommended)
- Features: VT-x (Intel) or AMD-V (AMD) virtualization support enabled in BIOS
- Clock Speed: 2.0 GHz minimum

**Memory:**
- Minimum: 8GB RAM
  - Proxmox Host: 4GB
  - Containers: 8GB (CT100: 4GB, CT101: 2GB, CT102: 1GB, CT103: 512MB)
- Recommended: 16GB RAM or more for production
- Swap: 4GB minimum on Proxmox host

**Storage:**
- Minimum: 100GB available storage
- Recommended: 200GB+ for production with backups and snapshots
- IOPS: 
  - Minimum: HDD (7200 RPM)
  - Recommended: SSD for PostgreSQL database performance
  - Optimal: NVMe SSD for production workloads

**Storage Layout:**
```
/var/lib/vz/template/cache/  - 1GB  (Container templates)
/var/lib/vz/images/          - 60GB (Container root filesystems)
/var/lib/vz/dump/            - 30GB (Backups)
Reserve for host             - 10GB (Proxmox host operations)
```

**Network:**
- 1 Gbps network interface minimum
- 10 Gbps recommended for production
- Support for bridge networking (Linux bridge)

### Hardware Validation

Before deployment, validate your hardware meets requirements:

```bash
# Check CPU cores
grep -c ^processor /proc/cpuinfo

# Check CPU virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo  # Should return > 0

# Check total memory
free -h

# Check available storage
df -h /var/lib/vz

# Check network interfaces
ip link show
```

## Software Requirements

### Proxmox VE Host

**Version Requirements:**
- Proxmox VE 9.1.0 or later (tested on 9.1.0)
- Backward compatible with Proxmox VE 9.0.x
- Kernel: 6.14+ recommended

**Repositories:**
- Standard Proxmox repositories enabled
- Enterprise repository optional (but not required)
- No-subscription repository enabled for updates

**Required Proxmox Packages:**
- `pve-manager` (core Proxmox package)
- `lxc` (Linux container support)
- `bridge-utils` (network bridge utilities)
- `python3` (for Ansible modules)

**Installation State:**
- Fresh installation or existing cluster node
- No conflicting container VMIDs: 100, 101, 102, 103
- No existing bridges: vmbr1, vmbr2 (will be created)

### Ansible Control Node

**Supported Operating Systems:**
- Linux distributions:
  - Ubuntu 22.04 LTS or later
  - Debian 12 (Bookworm) or later
  - RHEL 9+ / Rocky Linux 9+ / AlmaLinux 9+
  - Fedora 38+
- macOS 12 (Monterey) or later (with Homebrew)
- Windows via WSL2 (Ubuntu 22.04+ distribution)

**Required Software:**
- Python 3.10 or later
- pip (Python package manager)
- Git 2.30 or later
- SSH client (OpenSSH)

**Ansible Requirements:**
```yaml
ansible-core: ">=2.17.0" (2.20.0 recommended)
Python: ">=3.10"
```

**Required Ansible Collections:**
```yaml
community.general: "==12.1.0"
ansible.posix: "==2.1.0"
community.proxmox: "==1.4.0"
```

### Container Guest OS

**Templates Required:**
- Debian 13 (Trixie) standard template
- Template name: `debian-13-standard_13.1-2_amd64.tar.zst`
- Architecture: amd64
- Size: ~200MB compressed

## Network Requirements

### External Connectivity

**Required Outbound Access:**
- HTTPS (443): Package repositories, GitHub
- HTTP (80): Debian mirrors, package downloads
- DNS (53): Name resolution
- NTP (123): Time synchronization (recommended)

**Domains to Access:**
```
deb.debian.org          - Debian packages
github.com              - NetBox source code
pypi.org                - Python packages
download.proxmox.com    - Proxmox templates
```

### Network Configuration

**Bridge Requirements:**
- `vmbr0`: External/physical bridge (must exist)
  - Connected to physical network interface
  - DHCP or static configuration
  - Internet access

- `vmbr1`: Backend network (will be created)
  - Subnet: 10.100.0.0/24
  - Gateway: 10.100.0.1
  - Purpose: Database and cache isolation

- `vmbr2`: DMZ network (will be created)
  - Subnet: 10.100.1.0/24
  - Gateway: 10.100.1.1
  - Purpose: Application tier isolation

**IP Address Allocation:**
```
Backend Network (vmbr1 - 10.100.0.0/24):
  10.100.0.1   - Proxmox host gateway
  10.100.0.10  - NetBox application (CT 100)
  10.100.0.20  - PostgreSQL database (CT 101)
  10.100.0.30  - Valkey cache (CT 102)

DMZ Network (vmbr2 - 10.100.1.0/24):
  10.100.1.1   - Proxmox host gateway
  10.100.1.10  - NetBox application (CT 100)
  10.100.1.40  - Nginx proxy (CT 103)

External Network (vmbr0):
  DHCP or static - Nginx proxy (CT 103)
```

### Firewall Requirements

**Proxmox Host:**
- No inbound restrictions required (containers access via internal bridges)
- Outbound: Allow all (for package downloads)
- NAT/Masquerading: Will be configured for vmbr1 and vmbr2

**Container Access:**
- No external ports need to be opened initially
- HTTPS (443) will be available on CT 103 external IP after deployment
- Optional: SSH access to containers via Proxmox host

## Proxmox Host Requirements

### System Configuration

**Time Synchronization:**
```bash
# Verify NTP is running
systemctl status chronyd || systemctl status systemd-timesyncd

# Check time accuracy
timedatectl status
```

**Disk Space:**
```bash
# Check available space on container storage
df -h /var/lib/vz

# Required:
# /var/lib/vz: 100GB minimum free
```

**System Updates:**
```bash
# Update package lists
apt update

# Check for available updates
apt list --upgradable

# Apply security updates
apt upgrade -y
```

### SSH Access Configuration

**Root SSH Access (Key-based only, recommended):**
```bash
# Edit /etc/ssh/sshd_config to allow root login only with SSH keys
# This disables password authentication for root while allowing key-based access
PermitRootLogin prohibit-password

# For even better security, disable root SSH entirely and use a sudo-enabled user:
# PermitRootLogin no

# Restart SSH
systemctl restart sshd
```

**SSH Key Setup (Recommended):**
```bash
# On control node, generate SSH key
ssh-keygen -t ed25519 -C "ansible@netbox-deployment"

# Copy to Proxmox host
ssh-copy-id root@proxmox-host

# Test passwordless access
ssh root@proxmox-host "hostname"
```

### Resource Availability

**Check Available Resources:**
```bash
# Memory
free -h | grep Mem

# CPU load
uptime

# Storage
df -h /var/lib/vz

# Network
ip addr show
ip route show
```

**Verify No Conflicts:**
```bash
# Check for existing containers with target VMIDs
pct list | grep -E "(100|101|102|103)"

# Check for existing bridges
brctl show | grep -E "(vmbr1|vmbr2)"

# Check for conflicting IP addresses
ip addr show | grep -E "(10.100.0|10.100.1)"
```

## Control Node Requirements

### Software Installation

**Ubuntu/Debian:**
```bash
# Update package lists
apt update

# Install required packages
apt install -y python3 python3-pip git openssh-client

# Install Ansible
pip3 install ansible-core>=2.17.0

# Verify installation
ansible --version
python3 --version
git --version
```

**RHEL/Rocky/AlmaLinux:**
```bash
# Install EPEL repository
dnf install -y epel-release

# Install required packages
dnf install -y python3 python3-pip git openssh-clients

# Install Ansible
pip3 install ansible-core>=2.17.0

# Verify installation
ansible --version
```

**macOS (with Homebrew):**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python3 git ansible

# Verify installation
ansible --version
```

### Ansible Collections Installation

```bash
# Clone the repository
git clone https://github.com/nullroute-commits/netbox-proxmox-ansible.git
cd netbox-proxmox-ansible

# Install required collections
ansible-galaxy collection install -r requirements.yml

# Verify collections
ansible-galaxy collection list | grep -E "(community.general|ansible.posix|community.proxmox)"
```

## Pre-Deployment Validation

### Comprehensive Validation Script

Run this validation script on the Proxmox host before deployment:

```bash
#!/bin/bash
# NetBox Deployment Prerequisites Validation Script
# Run on Proxmox VE host as root

echo "=== NetBox Deployment Prerequisites Validation ==="
echo ""

# Check Proxmox version
echo "1. Checking Proxmox VE version..."
pveversion | head -1
pve_version=$(pveversion | head -1 | grep -oP 'pve-manager/\K[0-9.]+' | cut -d. -f1,2)
if (( $(echo "$pve_version >= 9.0" | bc -l) )); then
    echo "   ✓ Proxmox VE $pve_version (Compatible)"
else
    echo "   ✗ Proxmox VE $pve_version (Requires 9.0+)"
fi
echo ""

# Check CPU cores
echo "2. Checking CPU cores..."
cpu_cores=$(grep -c ^processor /proc/cpuinfo)
echo "   CPU cores: $cpu_cores"
if [ $cpu_cores -ge 2 ]; then
    echo "   ✓ Sufficient CPU cores"
else
    echo "   ✗ Insufficient CPU cores (minimum 2)"
fi
echo ""

# Check virtualization support
echo "3. Checking virtualization support..."
virt_support=$(egrep -c '(vmx|svm)' /proc/cpuinfo)
if [ $virt_support -gt 0 ]; then
    echo "   ✓ Virtualization support enabled"
else
    echo "   ✗ Virtualization support not detected"
fi
echo ""

# Check available memory
echo "4. Checking available memory..."
mem_available=$(free -g | awk '/^Mem:/ {print $7}')
echo "   Available memory: ${mem_available}GB"
if [ $mem_available -ge 8 ]; then
    echo "   ✓ Sufficient memory available"
else
    echo "   ⚠ Warning: Less than 8GB available"
fi
echo ""

# Check storage space
echo "5. Checking storage space..."
storage_available=$(df -BG /var/lib/vz | awk 'NR==2 {print $4}' | sed 's/G//')
echo "   Available storage: ${storage_available}GB"
if [ $storage_available -ge 100 ]; then
    echo "   ✓ Sufficient storage available"
else
    echo "   ⚠ Warning: Less than 100GB available"
fi
echo ""

# Check for conflicting VMIDs
echo "6. Checking for conflicting container VMIDs..."
conflicts=$(pct list | grep -E "(100|101|102|103)" | wc -l)
if [ $conflicts -eq 0 ]; then
    echo "   ✓ No conflicting VMIDs (100-103)"
else
    echo "   ✗ Found $conflicts conflicting VMIDs"
    pct list | grep -E "(100|101|102|103)"
fi
echo ""

# Check for conflicting bridges
echo "7. Checking for conflicting bridges..."
if brctl show | grep -qE "(vmbr1|vmbr2)"; then
    echo "   ⚠ Warning: vmbr1 or vmbr2 already exists"
    brctl show | grep -E "(vmbr1|vmbr2)"
else
    echo "   ✓ No conflicting bridges"
fi
echo ""

# Check internet connectivity
echo "8. Checking internet connectivity..."
if ping -c 2 debian.org > /dev/null 2>&1; then
    echo "   ✓ Internet connectivity available"
else
    echo "   ✗ No internet connectivity"
fi
echo ""

# Check DNS resolution
echo "9. Checking DNS resolution..."
if nslookup github.com > /dev/null 2>&1; then
    echo "   ✓ DNS resolution working"
else
    echo "   ✗ DNS resolution failed"
fi
echo ""

# Check required packages
echo "10. Checking required packages..."
for pkg in bridge-utils python3; do
    if dpkg -l | grep -q "^ii  $pkg "; then
        echo "   ✓ $pkg installed"
    else
        echo "   ⚠ $pkg not installed (will be installed during deployment)"
    fi
done
echo ""

echo "=== Validation Complete ==="
echo ""
echo "Prerequisites Summary:"
echo "- Review warnings (⚠) and errors (✗) above"
echo "- Ensure all critical checks pass (✓) before deployment"
echo "- Refer to automation_nation.git for hardware specifications"
echo "- See docs/PREREQUISITES.md for detailed requirements"
```

Save this script as `validate-prerequisites.sh` and run it:

```bash
chmod +x validate-prerequisites.sh
./validate-prerequisites.sh
```

### Expected Validation Results

All checks should show ✓ (pass) or ⚠ (warning). Any ✗ (fail) must be resolved before deployment:

- **Critical (must pass):**
  - Proxmox VE 9.0+
  - At least 2 CPU cores
  - Virtualization support enabled
  - Internet connectivity
  - DNS resolution
  - No conflicting VMIDs

- **Warnings (should pass):**
  - 8GB+ memory available
  - 100GB+ storage available
  - No existing vmbr1/vmbr2 bridges

## Additional Resources

- **Hardware Specifications**: [automation_nation.git](https://github.com/nullroute-commits/automation_nation.git)
- **Architecture Details**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment Guide**: [docs/GREENFIELD_DEPLOYMENT.md](GREENFIELD_DEPLOYMENT.md)
- **Version Information**: [VERSIONS.md](../VERSIONS.md)

## Support

If prerequisites validation fails:

1. Review the specific error messages
2. Use automation_nation.git to collect detailed system information
3. Check Proxmox VE documentation for host configuration
4. Verify network connectivity and DNS resolution
5. Create an issue in the repository with validation output and system info

---

**Last Updated:** December 2025  
**Proxmox Version:** 9.1+  
**Status:** Production Ready
