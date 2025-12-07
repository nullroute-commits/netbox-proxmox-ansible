# System Capability Analysis - automation_nation Integration

## Overview

This deployment uses **automation_nation** system information collection as the starting point for determining deployment configuration. The collected data is analyzed across three scopes:

1. **Networking** - Network interfaces, bridges, and connectivity
2. **Hardware Resources** - CPU, memory, storage capacity
3. **Software Resources** - Operating system, packages, virtualization

Based on the analysis, optimal deployment settings are automatically calculated and configured.

## Workflow

### 1. Collect System Information

On your Proxmox host, collect comprehensive system information:

```bash
# Clone automation_nation
git clone https://github.com/nullroute-commits/automation_nation.git
cd automation_nation

# Collect system information
./collect_info.sh -o /path/to/netbox-proxmox-ansible/system_info.json
```

This generates a JSON file containing:
- CPU architecture and cores
- Memory capacity and availability
- Disk devices and storage
- Network interfaces and configuration
- Installed packages
- Virtualization capabilities
- Kernel and OS information

### 2. Analyze System Capabilities

The deployment framework includes a Python script that parses the automation_nation output and generates deployment configuration:

```bash
cd /path/to/netbox-proxmox-ansible

# Analyze system and generate configuration
python3 scripts/parse_system_info.py system_info.json group_vars/all/generated_config.yml
```

Or use the Ansible playbook:

```bash
# Automated analysis with Ansible
ansible-playbook playbooks/analyze-system-capabilities.yml
```

### 3. Review Generated Configuration

The analysis generates optimal settings based on detected capabilities:

**Example output for a system with 16GB RAM, 8 cores:**

```yaml
containers:
  netbox:
    cores: 4
    memory: 6144  # 6GB
    swap: 2048
    rootfs_size: 32
  
  database:
    cores: 2
    memory: 4096  # 4GB
    swap: 1024
    rootfs_size: 16
  
  cache:
    cores: 1
    memory: 2048  # 2GB
    swap: 512
    rootfs_size: 8
  
  proxy:
    cores: 1
    memory: 1024  # 1GB
    swap: 256
    rootfs_size: 8
```

### 4. Deploy with Generated Configuration

The generated configuration is automatically used by deployment playbooks:

```bash
ansible-playbook playbooks/greenfield-deployment.yml --vault-password-file .vault_pass
```

## Scope Details

### Networking Scope

**What is Analyzed:**
- Detected network interfaces (eth0, ens*, etc.)
- Current IP addressing
- Interface states (up/down)
- MAC addresses

**What is Generated:**
- Primary interface identification
- Bridge configuration recommendations (vmbr0, vmbr1, vmbr2)
- NAT/masquerading configuration
- Network segment suggestions (10.100.0.0/24, 10.100.1.0/24)

**Example Network Configuration:**

```yaml
networking:
  detected_interfaces:
    - name: eth0
      ipv4: 192.168.1.100
      state: UP
  
  primary_interface: eth0
  
  suggested_bridges:
    vmbr0:
      comment: "External network (physical bridge)"
      ports: eth0
    vmbr1:
      comment: "Backend network (10.100.0.0/24)"
      cidr: "10.100.0.0/24"
      gateway: "10.100.0.1"
    vmbr2:
      comment: "DMZ network (10.100.1.0/24)"
      cidr: "10.100.1.0/24"
      gateway: "10.100.1.1"
```

### Hardware Resources Scope

**What is Analyzed:**
- CPU model and core count
- Total and available memory
- Disk devices and available storage
- Hardware virtualization support

**What is Generated:**
- Container CPU allocations
- Container memory allocations
- Disk space allocations
- Swap configurations
- Resource scaling based on total capacity

**Resource Scaling Tiers:**

| System RAM | NetBox RAM | Database RAM | Cache RAM | Proxy RAM |
|------------|------------|--------------|-----------|-----------|
| 8GB (minimum) | 4GB | 2GB | 1GB | 512MB |
| 16GB | 6GB | 4GB | 2GB | 1GB |
| 32GB+ | 8GB | 8GB | 4GB | 2GB |

| System CPU | NetBox CPU | Database CPU | Cache CPU | Proxy CPU |
|------------|------------|--------------|-----------|-----------|
| 2-3 cores | 2 | 2 | 1 | 1 |
| 4-7 cores | 3 | 2 | 1 | 1 |
| 8+ cores | 4 | 4 | 2 | 2 |

**Example Hardware Configuration:**

```yaml
hardware_resources:
  cpu:
    model: "AMD EPYC 7763 64-Core Processor"
    total_cores: 8
    available_cores: 6  # 2 reserved for host
  
  memory:
    total_gb: 16
    total_mb: 16384
    available_mb: 14336
    reserved_for_host_mb: 2048
  
  storage:
    root_available_gb: 150
    disk_info:
      - filesystem: /dev/root
        size: 200G
        available: 150G
  
  container_allocations:
    netbox: {cpu: 4, memory: 6144, swap: 2048, disk: 32}
    database: {cpu: 2, memory: 4096, swap: 1024, disk: 16}
    cache: {cpu: 1, memory: 2048, swap: 512, disk: 8}
    proxy: {cpu: 1, memory: 1024, swap: 256, disk: 8}
```

### Software Resources Scope

**What is Analyzed:**
- Operating system name and version
- Kernel version
- System architecture (x86_64, arm64, etc.)
- Virtualization type and role
- Installed package managers
- Prerequisite packages (python3, bridge-utils, iptables)

**What is Generated:**
- Software compatibility validation
- Package manager identification
- Prerequisite check results
- Warnings for missing packages
- Virtualization compatibility checks

**Example Software Configuration:**

```yaml
software_resources:
  operating_system:
    os_name: "Ubuntu"
    os_version: "22.04"
    kernel: "6.5.0-1025-azure"
    architecture: "x86_64"
  
  virtualization:
    type: "kvm"
    role: "host"
    hypervisor: "QEMU"
  
  package_managers:
    apt: 2847
    snap: 15
  
  prerequisites:
    python3: true
    bridge_utils: true
    iptables: true
```

## Validation and Warnings

The analysis performs comprehensive validation:

### Errors (Deployment Blocked)

These prevent deployment and must be resolved:

- **Insufficient Memory:** < 8GB total RAM
- **Insufficient Storage:** < 100GB available storage
- **Insufficient CPU:** < 2 CPU cores

### Warnings (Deployment Allowed)

These allow deployment but indicate suboptimal conditions:

- **Limited Memory:** 8-15GB (16GB+ recommended for production)
- **Limited Storage:** 100-199GB (200GB+ recommended)
- **Limited CPU:** 2-3 cores (4+ recommended for production)
- **Unexpected Virtualization:** Non-KVM/Proxmox environment
- **Missing Prerequisites:** bridge-utils, python3, iptables not detected

### Example Validation Output

```bash
$ python3 scripts/parse_system_info.py system_info.json generated_config.yml

Analyzing system information from automation_nation...
Warnings:
  - Limited memory: 8GB available, 16GB recommended for production
  - Limited CPU cores: 2 available, 4 recommended for production

✓ Deployment configuration written to: generated_config.yml

  Container allocations:
    - netbox: 2 CPU, 4096MB RAM, 32GB disk
    - database: 2 CPU, 2048MB RAM, 16GB disk
    - cache: 1 CPU, 1024MB RAM, 8GB disk
    - proxy: 1 CPU, 512MB RAM, 8GB disk
```

## Manual Configuration Override

You can override the generated configuration by editing the files:

### Option 1: Edit Generated Configuration

```bash
# Edit the generated file before deployment
vim group_vars/all/generated_config.yml
```

### Option 2: Merge with Existing Configuration

```bash
# Backup original
cp group_vars/all/containers.yml group_vars/all/containers.yml.original

# Manually merge values from generated_config.yml
vim group_vars/all/containers.yml
```

### Option 3: Use Static Configuration

```bash
# Don't run analyze-system-capabilities.yml
# Use the existing static configuration in group_vars/all/containers.yml
```

## Integration with Deployment Playbooks

The greenfield deployment can automatically use the generated configuration:

```yaml
# playbooks/greenfield-deployment.yml
vars_files:
  - ../group_vars/all/network.yml
  - ../group_vars/all/containers.yml
  - ../group_vars/all/generated_config.yml  # Auto-generated from system analysis
  - ../group_vars/all/versions.yml
  - ../group_vars/all/vault.yml
```

Ansible will merge variables, with later files taking precedence.

## Complete Deployment Workflow

### Step 1: Collect System Information

```bash
# On Proxmox host
cd /tmp
git clone https://github.com/nullroute-commits/automation_nation.git
cd automation_nation
./collect_info.sh -o /root/netbox-proxmox-ansible/system_info.json
```

### Step 2: Analyze and Generate Configuration

```bash
# On control node or Proxmox host
cd /root/netbox-proxmox-ansible
ansible-playbook playbooks/analyze-system-capabilities.yml
```

### Step 3: Review Configuration

```bash
# Review generated configuration
cat group_vars/all/generated_config.yml

# Check for warnings or errors
cat group_vars/all/generated_config.yml | grep -A 5 "warnings\|errors"
```

### Step 4: Deploy NetBox

```bash
# Run deployment with generated configuration
ansible-playbook playbooks/greenfield-deployment.yml --vault-password-file .vault_pass
```

### Step 5: Verify Deployment

```bash
# Verify deployment success
ansible-playbook playbooks/verify-deployment.yml
```

## Troubleshooting

### System Information Not Found

```
ERROR: System information not found at: system_info.json
```

**Solution:** Run automation_nation collection first:

```bash
cd /tmp
git clone https://github.com/nullroute-commits/automation_nation.git
cd automation_nation
./collect_info.sh -o /path/to/netbox-proxmox-ansible/system_info.json
```

### Insufficient Resources Error

```
ERROR: System does not meet deployment requirements:
  - Insufficient memory: 4GB available, 8GB minimum required
```

**Solution:** Upgrade hardware or adjust minimum requirements in `scripts/parse_system_info.py`.

### Python Dependencies Missing

```
ModuleNotFoundError: No module named 'yaml'
```

**Solution:** Install Python dependencies:

```bash
pip3 install pyyaml
```

## Advanced Usage

### Custom Resource Allocation

Edit `scripts/parse_system_info.py` to customize allocation logic:

```python
def _calculate_container_resources(self, hardware: Dict[str, Any]) -> Dict[str, Any]:
    # Customize allocation logic here
    allocations = {
        'netbox': {'cpu': 2, 'memory': 4096, ...},
        # ... your custom allocations
    }
    return allocations
```

### Integration with CI/CD

```yaml
# .github/workflows/deploy.yml
- name: Collect system information
  run: |
    ./automation_nation/collect_info.sh -o system_info.json

- name: Analyze and generate config
  run: |
    ansible-playbook playbooks/analyze-system-capabilities.yml

- name: Deploy
  run: |
    ansible-playbook playbooks/greenfield-deployment.yml
```

## Benefits

1. **Automatic Optimization:** Resources allocated based on actual hardware
2. **Validation:** Prevents deployment on insufficient hardware
3. **Scalability:** Automatically scales resource allocation with system capacity
4. **Documentation:** System capabilities documented in JSON
5. **Reproducibility:** Configuration can be regenerated from system state
6. **Flexibility:** Generated config can be reviewed and modified before deployment

## See Also

- [automation_nation.git](https://github.com/nullroute-commits/automation_nation.git) - System information collection
- [GREENFIELD_DEPLOYMENT.md](GREENFIELD_DEPLOYMENT.md) - Deployment guide
- [PREREQUISITES.md](PREREQUISITES.md) - System requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

---

**Last Updated:** December 2025  
**Status:** Production Ready  
**Tested With:** Proxmox VE 9.1+, automation_nation latest
