# Sprint Plan: NetBox-Proxmox Plugin Integration

**Sprint Goal:** Add support for the NetBox-Proxmox integration plugin to synchronize Proxmox VE infrastructure data with NetBox IPAM/DCIM.

**Created:** December 2025  
**Duration:** 1 Sprint (1-2 weeks)  
**Priority:** Medium-High

---

## Executive Summary

This sprint plan outlines the work required to integrate a NetBox-Proxmox plugin that enables bidirectional synchronization between Proxmox VE virtualization infrastructure and NetBox. This will allow automatic discovery and import of:

- Proxmox clusters
- Proxmox nodes (hypervisors)
- Virtual machines (VMs)
- LXC containers
- Storage resources
- Network configurations

---

## Architecture Design Review

### Current Architecture

The repository deploys NetBox in a three-tier containerized architecture on Proxmox VE:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Proxmox VE 9.0 Host                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  CT 100     │  │  CT 101     │  │  CT 102     │             │
│  │  NetBox     │  │  PostgreSQL │  │  Valkey     │             │
│  │  App        │  │  Database   │  │  Cache      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                │                │                     │
│         └────────────────┴────────────────┘                     │
│                     Backend Network                             │
│                     (10.100.0.0/24)                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                                                │
│  │  CT 103     │                                                │
│  │  Nginx      │───── DMZ Network (10.100.1.0/24)               │
│  │  Proxy      │                                                │
│  └─────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Isolated Networks**: Backend (database/cache) and DMZ (application) separation
2. **Proxmox API Access**: The plugin will need to access Proxmox VE API
3. **Container Execution**: All tasks execute via `pct exec` on Proxmox host
4. **Plugin Architecture**: Plugins are installed via pip in NetBox virtualenv

### Plugin Selection Analysis

| Plugin | Version | Compatibility | Features | Recommendation |
|--------|---------|---------------|----------|----------------|
| `netbox-proxmox-import` | 1.1.2 | NetBox 4.2+ | Import/sync, UI management | **Recommended** |
| `netbox-proxbox-stable` | 0.0.6 | NetBox 4.1.6+ | Conservative, stable | Alternative |
| `netbox-proxbox` | 0.0.6b2 | NetBox 4.x | Beta, more features | Development |
| `netbox-proxmox-automation` | 2025.11.02 | NetBox 4.x | Event-driven automation | Add-on |

**Selected Plugin:** `netbox-proxmox-import==1.1.2`

**Rationale:**
- Stable release (not beta)
- Active maintenance (July 2025 release)
- Full NetBox 4.x compatibility
- Clean import/sync workflow with UI
- Read-only option for safe operation

---

## Sprint Backlog

### Epic 1: Plugin Installation (Priority: Critical)

#### Story 1.1: Update Role Defaults

**Acceptance Criteria:**
- [ ] Add `netbox-proxmox-import` to `netbox_app_plugins` list with pinned version
- [ ] Add plugin module name to `netbox_app_plugin_modules`
- [ ] Document new plugin variables

**Implementation:**

```yaml
# roles/netbox_app/defaults/main.yml additions

# NetBox plugins with pinned versions (updated)
netbox_app_plugins:
  - "netbox-plugin-dns==1.4.4"
  - "netbox-secrets==2.4.1"
  - "netbox-acls==1.9.1"
  - "netbox-bgp==0.17.0"
  - "netbox-inventory==2.4.1"
  - "netbox-floorplan-plugin==0.8.0"
  - "netbox-reorder-rack==1.1.4"
  - "netbox-proxmox-import==1.1.2"  # NEW: Proxmox integration

# Plugin module names for configuration.py (updated)
netbox_app_plugin_modules:
  - "netbox_dns"
  - "netbox_secrets"
  - "netbox_acls"
  - "netbox_bgp"
  - "netbox_inventory"
  - "netbox_floorplan"
  - "netbox_reorder_rack"
  - "netbox_proxmox_import"  # NEW: Proxmox integration
```

#### Story 1.2: Add Plugin Configuration Variables

**Acceptance Criteria:**
- [ ] Create configurable plugin settings
- [ ] Support multiple Proxmox cluster connections
- [ ] Allow enabling/disabling sync features

**Implementation:**

```yaml
# roles/netbox_app/defaults/main.yml additions

# NetBox-Proxmox-Import Plugin Configuration
netbox_app_proxmox_plugin_enabled: true
netbox_app_proxmox_clusters: []
# Example cluster configuration:
#   - name: "primary-cluster"
#     host: "proxmox.example.com"
#     port: 8006
#     user: "netbox@pve"
#     # password: Set via vault as vault_proxmox_api_password
#     verify_ssl: true
#     sync_vms: true
#     sync_containers: true
#     sync_storage: true

# Plugin-specific settings
netbox_app_proxmox_import_config:
  verify_ssl: true
  sync_interval: 3600  # seconds
  read_only: false     # Set to true for import-only mode
```

---

### Epic 2: Configuration Templates (Priority: High)

#### Story 2.1: Update NetBox Configuration Template

**Acceptance Criteria:**
- [ ] Add PLUGINS_CONFIG section for netbox_proxmox_import
- [ ] Support conditional configuration based on clusters defined
- [ ] Handle secrets securely via Ansible Vault

**Implementation:**

Update `roles/netbox_app/tasks/main.yml` configuration template:

```python
# In configuration.py (PLUGINS_CONFIG section)
PLUGINS_CONFIG = {
    {% if netbox_app_proxmox_plugin_enabled %}
    "netbox_proxmox_import": {
        "verify_ssl": {{ netbox_app_proxmox_import_config.verify_ssl | default(true) | ternary('True', 'False') }},
    },
    {% endif %}
}
```

#### Story 2.2: Add Vault Variables Template

**Acceptance Criteria:**
- [ ] Add Proxmox API credentials to vault template
- [ ] Document security requirements
- [ ] Provide example configuration

**Implementation:**

```yaml
# group_vars/all/vault.yml additions
vault_proxmox_api_user: "netbox@pve"
vault_proxmox_api_password: "CHANGE_ME"
vault_proxmox_api_token_id: ""  # Optional: Token ID for API token auth
vault_proxmox_api_token_secret: ""  # Optional: Token secret
```

---

### Epic 3: Network Connectivity (Priority: High)

#### Story 3.1: Ensure Proxmox API Access

**Acceptance Criteria:**
- [ ] NetBox container can reach Proxmox API (port 8006)
- [ ] SSL/TLS verification configurable
- [ ] Document firewall requirements

**Implementation:**

The NetBox container (CT 100) needs network access to the Proxmox API. Options:

**Option A: Backend Network (Recommended)**
- Add Proxmox host IP route to backend network
- NetBox connects to `10.100.0.1:8006` (gateway)

**Option B: External Network**
- Add third network interface to CT 100
- Connect directly to Proxmox management network

**Firewall Rules:**
```bash
# Allow NetBox to access Proxmox API
iptables -A FORWARD -s 10.100.0.10 -d <proxmox-ip> -p tcp --dport 8006 -j ACCEPT
```

#### Story 3.2: Create Proxmox API User

**Acceptance Criteria:**
- [ ] Create dedicated API user for NetBox integration
- [ ] Assign minimum required permissions
- [ ] Document permission requirements

**Implementation:**

Create Proxmox user via `pveum`:

```bash
# Create role with minimum permissions
pveum role add NetBoxSync -privs "VM.Audit,VM.Monitor,Datastore.Audit,SDN.Audit,Sys.Audit,Pool.Audit"

# Create user
pveum user add netbox@pve -comment "NetBox Integration"

# Assign role
pveum acl modify / -user netbox@pve -role NetBoxSync

# Set password (or create API token)
pveum passwd netbox@pve
```

---

### Epic 4: Documentation Updates (Priority: Medium)

#### Story 4.1: Update VERSIONS.md

**Acceptance Criteria:**
- [ ] Add netbox-proxmox-import to plugin list
- [ ] Document version compatibility
- [ ] Add update policy for plugin

**Implementation:**

```markdown
## NetBox Plugins

| Plugin | Version | Repository |
|--------|---------|------------|
| netbox-plugin-dns | 1.4.4 | GitHub |
| netbox-secrets | 2.4.1 | GitHub |
| netbox-acls | 1.9.1 | GitHub |
| netbox-bgp | 0.17.0 | GitHub |
| netbox-inventory | 2.4.1 | GitHub |
| netbox-floorplan-plugin | 0.8.0 | GitHub |
| netbox_reorder_rack | 1.1.4 | GitHub |
| **netbox-proxmox-import** | **1.1.2** | **PyPI** | # NEW
```

#### Story 4.2: Update README.md

**Acceptance Criteria:**
- [ ] Add plugin to feature list
- [ ] Document Proxmox integration capability
- [ ] Add setup instructions

**Implementation:**

```markdown
## NetBox Plugins

All plugins pinned to latest stable versions (December 2025):

1. **netbox-plugin-dns** (v1.4.4) - DNS zone/record management
2. **netbox-secrets** (v2.4.1) - Encrypted secret storage
3. **netbox-acls** (v1.9.1) - Access control lists
4. **netbox-bgp** (v0.17.0) - BGP peering management
5. **netbox-inventory** (v2.4.1) - Enhanced inventory tracking
6. **netbox-floorplan-plugin** (v0.8.0) - Datacenter floor planning
7. **netbox-reorder-rack** (v1.1.4) - Rack device reordering
8. **netbox-proxmox-import** (v1.1.2) - Proxmox VE integration  # NEW
```

#### Story 4.3: Create Proxmox Integration Guide

**Acceptance Criteria:**
- [ ] Create `docs/PROXMOX_INTEGRATION.md`
- [ ] Document setup process
- [ ] Provide troubleshooting guide

**Content Outline:**

1. Overview
2. Prerequisites
3. Proxmox API User Setup
4. NetBox Plugin Configuration
5. Synchronization Features
6. Troubleshooting
7. Security Considerations

---

### Epic 5: Testing and Validation (Priority: High)

#### Story 5.1: Plugin Installation Test

**Acceptance Criteria:**
- [ ] Plugin installs without errors
- [ ] Plugin appears in NetBox admin
- [ ] No dependency conflicts

**Test Commands:**

```bash
# Verify installation
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && pip list | grep proxmox"

# Check NetBox plugin status
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  cd /opt/netbox/netbox && python3 manage.py showmigrations netbox_proxmox_import"
```

#### Story 5.2: Connectivity Test

**Acceptance Criteria:**
- [ ] NetBox can reach Proxmox API
- [ ] API authentication succeeds
- [ ] SSL verification works (if enabled)

**Test Commands:**

```bash
# Test API connectivity from NetBox container
pct exec 100 -- bash -c "curl -k https://<proxmox-ip>:8006/api2/json/version"

# Test authentication
pct exec 100 -- bash -c "curl -k -d 'username=netbox@pve&password=<password>' \
  https://<proxmox-ip>:8006/api2/json/access/ticket"
```

---

## Implementation Order

### Phase 1: Core Integration (Stories 1.1, 1.2, 2.1)
- Add plugin to defaults
- Update configuration template
- Run ansible-lint validation

### Phase 2: Network & Security (Stories 3.1, 3.2, 2.2)
- Configure network access
- Create Proxmox API user
- Set up vault credentials

### Phase 3: Testing (Stories 5.1, 5.2)
- Test plugin installation
- Verify connectivity
- Test synchronization

### Phase 4: Documentation (Stories 4.1, 4.2, 4.3)
- Update version documentation
- Update README
- Create integration guide

---

## Definition of Done

### Per Story:
- [ ] Code changes implemented
- [ ] ansible-lint passes with no errors
- [ ] Changes tested on development environment
- [ ] Documentation updated
- [ ] Peer review completed

### Sprint Completion:
- [ ] Plugin successfully installs
- [ ] Configuration template includes plugin settings
- [ ] Network connectivity verified
- [ ] Documentation complete
- [ ] All acceptance criteria met

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Plugin compatibility issues | High | Low | Pin to tested version, test before production |
| Network connectivity problems | Medium | Medium | Document firewall rules, test connectivity |
| API authentication failures | Medium | Low | Use API tokens instead of passwords |
| Plugin updates break sync | Medium | Medium | Pin version, test updates in dev first |

---

## Security Considerations

1. **API Credentials**
   - Store in Ansible Vault (encrypted)
   - Use API tokens instead of passwords where possible
   - Create dedicated user with minimum permissions

2. **Network Security**
   - Restrict API access to NetBox container IP only
   - Enable SSL verification in production
   - Use firewall rules to limit API exposure

3. **Read-Only Mode**
   - Consider enabling read-only mode initially
   - Test write operations in development first

---

## Version Reference

### netbox-proxmox-import 1.1.2

- **Release Date:** July 3, 2025
- **Compatibility:** NetBox 4.2+
- **Features:**
  - Cluster discovery and import
  - VM and container synchronization
  - Storage resource tracking
  - UI management interface
  - Read-only operation mode

### Dependencies

```
proxmoxer>=2.0.0
requests>=2.28.0
```

---

## Post-Implementation Tasks

1. **Initial Synchronization**
   - Configure cluster connection in NetBox UI
   - Run initial full sync
   - Verify imported data accuracy

2. **Ongoing Maintenance**
   - Schedule periodic syncs (cron or NetBox scheduled jobs)
   - Monitor sync status
   - Review and merge duplicate objects

3. **Plugin Updates**
   - Monitor PyPI for security updates
   - Test new versions in development
   - Update pinned version after validation

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Status:** Ready for Implementation
