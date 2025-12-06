# Software Versions - Pinned Stable Releases

This document lists all software versions used in this deployment, pinned to stable releases as of December 2025.

## Host System

| Component | Version | Notes |
|-----------|---------|-------|
| Proxmox VE | 9.0.3 | Latest stable (9.0.0) |
| Kernel | 6.14.8-2-pve | Proxmox kernel |
| Debian | 13.1 (Trixie) | Container OS |

## Core Services

### Database Tier (CT 101)

| Component | Version | Package |
|-----------|---------|---------|
| PostgreSQL | 17.6 | postgresql-17 |
| PostgreSQL Client | 17.6 | postgresql-client-17 |
| Debian | 13.1 | debian-13-standard |

**PostgreSQL Release Info:**
- Release: 17.6 (December 5, 2024)
- Debian Package: 17.6-0+deb13u1
- Support: Until November 2029

### Cache Tier (CT 102)

| Component | Version | Package |
|-----------|---------|---------|
| Valkey | 8.1.1 | valkey-server |
| Malloc | jemalloc-5.3.0 | System library |
| Debian | 13.1 | debian-13-standard |

**Valkey Release Info:**
- Release: 8.1.1 (Latest stable)
- Redis Compatible: 7.2+
- Build: 42e971026a5c6f02

### Application Tier (CT 100)

| Component | Version | Package/Source |
|-----------|---------|----------------|
| NetBox | v4.4.7 | GitHub release (recommended) |
| Python | 3.13.5 | python3 |
| Gunicorn | 23.0.0 | PyPI package |
| Debian | 13.1 | debian-13-standard |

**NetBox Release Info:**
- Latest Stable: v4.4.7
- Current Branch: main (commit: da1e0f4)
- Recommendation: Use v4.4.7 for production

**Python Release Info:**
- Release: 3.13.5 (Latest stable)
- Support: Until October 2029

### Proxy Tier (CT 103)

| Component | Version | Package |
|-----------|---------|---------|
| Nginx | 1.26.3 | nginx |
| OpenSSL | 3.3+ | openssl |
| Debian | 13.1 | debian-13-standard |

**Nginx Release Info:**
- Release: 1.26.3 (Stable branch)
- Mainline: 1.27.x (development)

## NetBox Plugins

All plugins pinned to latest stable versions as of December 2025:

| Plugin | Version | Repository |
|--------|---------|------------|
| netbox-plugin-dns | 1.4.4 | [GitHub](https://github.com/auroraresearchlab/netbox-dns) |
| netbox-secrets | 2.4.1 | [GitHub](https://github.com/Onemind-Services-LLC/netbox-secrets) |
| netbox-acls | 1.9.1 | [GitHub](https://github.com/netbox-community/netbox-acls) |
| netbox-bgp | 0.17.0 | [GitHub](https://github.com/netbox-community/netbox-bgp) |
| netbox-inventory | 2.4.1 | [GitHub](https://github.com/ArnesSI/netbox-inventory) |
| netbox-floorplan-plugin | 0.8.0 | [GitHub](https://github.com/netbox-community/netbox-floorplan) |
| netbox_reorder_rack | 1.1.4 | [GitHub](https://github.com/minitriga/netbox-reorder-rack) |

## Ansible Dependencies

| Component | Minimum Version | Recommended | EOL |
|-----------|----------------|-------------|-----|
| ansible-core | 2.17.0 | **2.20.0** | Nov 2026 |
| Python (Control Node) | 3.10 | 3.12+ | Oct 2028 |
| community.general | 12.1.0 | **12.1.0** | - |
| ansible.posix | 2.1.0 | **2.1.0** | - |
| community.proxmox | 1.4.0 | **1.4.0** | - |
| ansible-lint | 25.12.0 | **25.12.0** | - |

**Note:** All collection versions are pinned in `requirements.yml` for reproducible deployments.

## Container Template

| Component | Version | Source |
|-----------|---------|--------|
| Template | debian-13-standard_13.1-2_amd64.tar.zst | Proxmox repository |
| Architecture | amd64 | 64-bit |
| Size | ~200MB | Compressed |

## Version Compatibility Matrix

### NetBox Compatibility

| NetBox Version | Python | PostgreSQL | Redis/Valkey |
|----------------|--------|------------|--------------|
| 4.4.7 (current) | 3.10-3.13 | 15+ | 7.0+ |
| 4.3.x | 3.10-3.12 | 15+ | 7.0+ |
| 4.2.x | 3.10-3.12 | 15+ | 7.0+ |

### PostgreSQL Compatibility

| PostgreSQL | Debian | EOL Date |
|------------|--------|----------|
| 17.6 | 13+ | November 2029 |
| 16.x | 12+ | November 2028 |
| 15.x | 11+ | November 2027 |

### Python Compatibility

| Python | NetBox | EOL Date |
|--------|--------|----------|
| 3.13 | 4.4+ | October 2029 |
| 3.12 | 4.2+ | October 2028 |
| 3.11 | 4.0+ | October 2027 |

## Recommended Version Pinning for Ansible

### In requirements.yml

```yaml
---
# Ansible Galaxy Requirements
# Pinned to stable versions as of December 2025
# Requires ansible-core >= 2.17.0

collections:
  # General purpose modules and plugins
  - name: community.general
    version: "==12.1.0"

  # POSIX system modules (sysctl, authorized_key, etc.)
  - name: ansible.posix
    version: "==2.1.0"

  # Proxmox VE management modules (replaces deprecated community.general.proxmox)
  - name: community.proxmox
    version: "==1.4.0"
```

### In group_vars/all/versions.yml

```yaml
---
# Software versions - pinned to stable releases

# Container template
debian_template: "debian-13-standard_13.1-2_amd64.tar.zst"
debian_version: "13.1"

# PostgreSQL
postgresql_version: "17"
postgresql_package_version: "17.6-0+deb13u1"

# Valkey
valkey_version: "8.1.1"

# NetBox
netbox_version: "v4.4.7"  # Git tag
netbox_branch: "main"      # Alternative for latest

# Python
python_version: "3.13"

# Nginx
nginx_version: "1.26"  # Stable branch

# Gunicorn
gunicorn_version: "23.0.0"

# Ansible Dependencies - Pinned versions
ansible_core_version: "2.20.0"
ansible_min_version: "2.17.0"

# Ansible Collections - Pinned versions
ansible_collections:
  community_general:
    name: "community.general"
    version: "12.1.0"
  ansible_posix:
    name: "ansible.posix"
    version: "2.1.0"
  community_proxmox:
    name: "community.proxmox"
    version: "1.4.0"

# Plugins (exact versions)
netbox_plugins_versions:
  netbox_plugin_dns: "1.4.4"
  netbox_secrets: "2.4.1"
  netbox_acls: "1.9.1"
  netbox_bgp: "0.17.0"
  netbox_inventory: "2.4.1"
  netbox_floorplan_plugin: "0.8.0"
  netbox_reorder_rack: "1.1.4"
```

### In roles/netbox_app/defaults/main.yml

```yaml
---
# NetBox version configuration
netbox_app_version: "{{ netbox_version | default('v4.4.7') }}"
netbox_app_repository: "https://github.com/netbox-community/netbox.git"

# Python packages with pinned versions
netbox_app_plugins:
  - "gunicorn==23.0.0"
  - "netbox-plugin-dns==1.4.4"
  - "netbox-secrets==2.4.1"
  - "netbox-acls==1.9.1"
  - "netbox-bgp==0.17.0"
  - "netbox-inventory==2.4.1"
  - "netbox-floorplan-plugin==0.8.0"
  - "netbox-reorder-rack==1.1.4"
```

## Update Policy

### Security Updates

Apply immediately:
- PostgreSQL security releases
- Python security patches
- Debian security updates
- Critical NetBox CVEs

### Minor Updates

Test before applying:
- NetBox minor versions (4.4.x → 4.4.y)
- Plugin updates
- Python minor versions

### Major Updates

Plan and test thoroughly:
- NetBox major versions (4.x → 5.x)
- PostgreSQL major versions (17 → 18)
- Python major versions (3.13 → 3.14)

## Version Update Commands

### Check Current Versions

```bash
# PostgreSQL
pct exec 101 -- psql --version

# Valkey
pct exec 102 -- valkey-server --version

# NetBox
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox && git describe --tags"

# Nginx
pct exec 103 -- nginx -v

# Python
pct exec 100 -- python3 --version

# Plugins
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && pip list | grep netbox"
```

### Check for Updates

```bash
# Latest NetBox release
curl -s https://api.github.com/repos/netbox-community/netbox/releases/latest | grep tag_name

# PostgreSQL available versions
apt-cache madison postgresql-17

# Debian updates
pct exec 100 -- apt update && pct exec 100 -- apt list --upgradable
```

## Version History

| Date | Change | Version |
|------|--------|---------|
| 2025-12-05 | Initial deployment | All stable releases documented |
| 2025-12-05 | Version pinning implemented | Locked to stable versions |

## References

- NetBox Releases: https://github.com/netbox-community/netbox/releases
- PostgreSQL Releases: https://www.postgresql.org/support/versioning/
- Python Releases: https://www.python.org/downloads/
- Valkey Releases: https://github.com/valkey-io/valkey/releases
- Nginx Releases: https://nginx.org/en/CHANGES

---

**Last Updated:** December 5, 2025  
**Next Review:** March 2026 (Quarterly)
