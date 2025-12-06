# Sprint Plan: Ansible and Red Hat Standards Update

**Sprint Goal:** Update the NetBox on Proxmox VE Ansible automation repository to comply with latest stable Ansible versions and Red Hat best practices.

**Created:** December 2025  
**Duration:** 1-2 Sprints (2-4 weeks)  
**Priority:** High

---

## Executive Summary

This sprint plan outlines the work required to update the `netbox-proxmox-ansible` repository to:
1. Pin all dependencies to latest stable versions
2. Comply with Red Hat Ansible automation best practices
3. Improve code quality through linting and standardized structure

---

## Current State Analysis

### Software Versions (Current → Target)

| Component | Current Version | Target Version | Notes |
|-----------|----------------|----------------|-------|
| ansible-core | 2.14.0+ | **2.20.0** | Latest stable (Nov 2025) |
| Ansible (package) | Not specified | **12.x** | Includes ansible-core 2.20 |
| community.general | >=8.0.0 | **12.1.0** | Pin to exact version |
| ansible.posix | >=1.5.0 | **2.1.0** | Pin to exact version |
| community.proxmox | Not specified | **1.4.0** | New requirement for Proxmox |
| ansible-lint | Not configured | **25.12.0** | Add for code quality |

### Repository Structure Gaps

| Gap | Current State | Target State |
|-----|--------------|--------------|
| Role defaults | Missing | Add `defaults/main.yml` to all roles |
| Role metadata | Missing | Add `meta/main.yml` to all roles |
| Linting config | Missing | Add `.ansible-lint` and `.yamllint` |
| Variable prefixing | Inconsistent | Prefix all role vars with role name |
| Handlers | Incomplete | Add proper handlers to all roles |
| Documentation | Partial | Complete role README files |

---

## Sprint Backlog

### Epic 1: Dependency Version Pinning (Priority: Critical)

#### Story 1.1: Update requirements.yml
**Acceptance Criteria:**
- [ ] Pin `community.general` to version `12.1.0`
- [ ] Pin `ansible.posix` to version `2.1.0`
- [ ] Add `community.proxmox` collection version `1.4.0`
- [ ] Add version constraints compatible with ansible-core 2.17+

**Implementation:**
```yaml
---
collections:
  - name: community.general
    version: "==12.1.0"
  - name: ansible.posix
    version: "==2.1.0"
  - name: community.proxmox
    version: "==1.4.0"
```

#### Story 1.2: Update versions.yml
**Acceptance Criteria:**
- [ ] Update `ansible_min_version` to `2.17.0` (minimum for new collections)
- [ ] Update `ansible_recommended_version` to `2.20.0`
- [ ] Add collection version information
- [ ] Document ansible-lint version

---

### Epic 2: Red Hat Standards Compliance (Priority: High)

#### Story 2.1: Add Role Defaults Files
**Acceptance Criteria:**
- [ ] Create `defaults/main.yml` for each role
- [ ] Move configurable variables to defaults
- [ ] Use role name prefix for all variables
- [ ] Document each variable with comments

**Roles to Update:**
1. `debian_base`
2. `netbox_app`
3. `nginx_proxy`
4. `postgresql`
5. `proxmox_container`
6. `proxmox_host`
7. `proxmox_network`
8. `valkey`

#### Story 2.2: Add Role Metadata Files
**Acceptance Criteria:**
- [ ] Create `meta/main.yml` for each role
- [ ] Specify role dependencies
- [ ] Define minimum Ansible version
- [ ] Add Galaxy metadata (author, license, platforms)

**Template:**
```yaml
---
galaxy_info:
  author: NetBox Proxmox Team
  description: <role description>
  license: MIT
  min_ansible_version: "2.17"
  platforms:
    - name: Debian
      versions:
        - trixie
    - name: Proxmox
      versions:
        - "9"
  galaxy_tags:
    - netbox
    - proxmox
dependencies: []
```

#### Story 2.3: Standardize Variable Naming
**Acceptance Criteria:**
- [ ] Prefix all role variables with role name
- [ ] Update all references in tasks
- [ ] Maintain backward compatibility with variable mapping

**Naming Convention:**
| Role | Variable Prefix | Example |
|------|-----------------|---------|
| debian_base | `debian_base_` | `debian_base_packages` |
| postgresql | `postgresql_` | `postgresql_version` |
| valkey | `valkey_` | `valkey_bind_address` |
| netbox_app | `netbox_app_` | `netbox_app_version` |
| nginx_proxy | `nginx_proxy_` | `nginx_proxy_ssl_cert` |
| proxmox_host | `proxmox_host_` | `proxmox_host_packages` |
| proxmox_network | `proxmox_network_` | `proxmox_network_bridges` |
| proxmox_container | `proxmox_container_` | `proxmox_container_template` |

#### Story 2.4: Add Handler Files
**Acceptance Criteria:**
- [ ] Create/update `handlers/main.yml` for each role
- [ ] Define idempotent service restart handlers
- [ ] Link tasks to handlers via notify

---

### Epic 3: Code Quality Configuration (Priority: High)

#### Story 3.1: Add ansible-lint Configuration
**Acceptance Criteria:**
- [ ] Create `.ansible-lint` configuration file
- [ ] Configure appropriate rule exclusions
- [ ] Set minimum Ansible version
- [ ] Configure offline mode for collections

**Configuration:**
```yaml
---
profile: production
offline: false
exclude_paths:
  - .git/
  - .github/
  - group_vars/all/vault.yml
skip_list:
  - yaml[line-length]  # Allow longer lines for readability
  - name[casing]       # Allow flexible task naming
warn_list:
  - command-instead-of-shell
  - command-instead-of-module
```

#### Story 3.2: Add yamllint Configuration
**Acceptance Criteria:**
- [ ] Create `.yamllint` configuration file
- [ ] Configure line length limits
- [ ] Set indentation rules
- [ ] Allow truthy values for Ansible compatibility

**Configuration:**
```yaml
---
extends: default
rules:
  line-length:
    max: 160
    level: warning
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no']
  comments:
    require-starting-space: true
    min-spaces-from-content: 1
  indentation:
    spaces: 2
    indent-sequences: true
```

---

### Epic 4: Documentation Updates (Priority: Medium)

#### Story 4.1: Update README.md
**Acceptance Criteria:**
- [ ] Update Ansible version requirements
- [ ] Add ansible-lint badge
- [ ] Document collection dependencies
- [ ] Add development/contribution guide updates

#### Story 4.2: Update VERSIONS.md
**Acceptance Criteria:**
- [ ] Update Ansible Dependencies section
- [ ] Add collection version details
- [ ] Add ansible-lint version
- [ ] Update compatibility matrix

#### Story 4.3: Add Role README Files
**Acceptance Criteria:**
- [ ] Create README.md for each role
- [ ] Document all variables
- [ ] Provide usage examples
- [ ] List dependencies

---

### Epic 5: ansible.cfg Updates (Priority: Medium)

#### Story 5.1: Update ansible.cfg
**Acceptance Criteria:**
- [ ] Add collections path configuration
- [ ] Enable callback plugins per Red Hat guidelines
- [ ] Add interpreter discovery configuration
- [ ] Configure remote_tmp appropriately

**Updates:**
```ini
[defaults]
# Add/Update these settings
interpreter_python = auto_silent
collections_path = ./collections:~/.ansible/collections
any_errors_fatal = false

[galaxy]
server_list = galaxy

[galaxy_server.galaxy]
url = https://galaxy.ansible.com/
```

---

## Definition of Done

### Per Story:
- [ ] Code changes implemented
- [ ] ansible-lint passes with no errors
- [ ] yamllint passes with no errors
- [ ] Changes tested locally (where applicable)
- [ ] Documentation updated
- [ ] Peer review completed

### Sprint Completion:
- [ ] All stories completed
- [ ] Full ansible-lint run passes
- [ ] README.md updated with new requirements
- [ ] VERSIONS.md reflects all version changes
- [ ] All roles have proper structure
- [ ] Code review completed

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes in ansible-core 2.20 | High | Test playbooks thoroughly, review porting guides |
| Collection API changes | Medium | Pin exact versions, document compatibility |
| Existing playbook failures | Medium | Maintain backward compatibility where possible |

---

## Testing Strategy

### Pre-Merge Testing
1. **Syntax Check**
   ```bash
   ansible-playbook --syntax-check playbooks/site.yml
   ```

2. **Lint Check**
   ```bash
   ansible-lint
   yamllint .
   ```

3. **Dry Run** (on test environment)
   ```bash
   ansible-playbook playbooks/site.yml --check --diff
   ```

---

## Implementation Order

1. **Phase 1: Foundation** (Stories 1.1, 1.2, 3.1, 3.2, 5.1)
   - Update dependencies and add linting configuration
   - This enables validation of subsequent changes

2. **Phase 2: Role Structure** (Stories 2.1, 2.2)
   - Add defaults and metadata to all roles
   - Establishes proper role structure

3. **Phase 3: Standards Compliance** (Stories 2.3, 2.4)
   - Standardize variable naming
   - Add handlers

4. **Phase 4: Documentation** (Stories 4.1, 4.2, 4.3)
   - Update all documentation
   - Add role READMEs

---

## Appendix: Version Reference

### Ansible Core 2.20.0 Key Changes
- New templating engine improvements
- Enhanced module parameter validation
- Improved error messaging
- Python 3.10+ required on control node

### community.general 12.1.0 Key Notes
- Compatible with ansible-core 2.17.0+
- New modules and plugins
- Bug fixes for Proxmox modules (migrating to community.proxmox)

### community.proxmox 1.4.0 Key Notes
- Replaces deprecated community.general.proxmox modules
- Full Proxmox VE 8.x and 9.x support
- LXC container management
- VM management
- Snapshot and backup modules

### ansible.posix 2.1.0 Key Notes
- POSIX system modules (sysctl, authorized_key, etc.)
- Compatible with ansible-core 2.15.0+

---

**Document Version:** 1.0  
**Last Updated:** December 2025
