# Ansible Automation Design

## Project Structure

```
netbox-proxmox-ansible/
├── ansible.cfg                    # Ansible configuration
├── requirements.yml               # Galaxy collections/roles
├── inventory/
│   ├── production/
│   │   ├── hosts.yml             # Inventory hosts
│   │   └── group_vars/
│   │       ├── all.yml           # Global variables
│   │       ├── proxmox.yml       # Proxmox-specific vars
│   │       └── netbox.yml        # NetBox-specific vars
│   └── staging/                  # Staging environment (optional)
├── playbooks/
│   ├── site.yml                  # Master playbook
│   ├── 01-proxmox-setup.yml      # Proxmox host configuration
│   ├── 02-network-setup.yml      # Network bridges and routing
│   ├── 03-containers-create.yml  # LXC container creation
│   ├── 04-database-setup.yml     # PostgreSQL installation/config
│   ├── 05-cache-setup.yml        # Valkey installation/config
│   ├── 06-netbox-setup.yml       # NetBox installation/config
│   ├── 07-proxy-setup.yml        # Nginx installation/config
│   └── 99-teardown.yml           # Cleanup/removal playbook
├── roles/
│   ├── proxmox_host/             # Proxmox host preparation
│   ├── proxmox_network/          # Network bridge configuration
│   ├── proxmox_container/        # LXC container management
│   ├── debian_base/              # Debian container baseline
│   ├── postgresql/               # PostgreSQL setup
│   ├── valkey/                   # Valkey/Redis setup
│   ├── netbox_app/               # NetBox application
│   └── nginx_proxy/              # Nginx reverse proxy
├── group_vars/
│   └── all/
│       ├── network.yml           # Network configuration
│       ├── containers.yml        # Container definitions
│       └── vault.yml             # Encrypted secrets
├── templates/                     # Jinja2 templates
│   ├── network/
│   │   └── interfaces.j2
│   ├── postgresql/
│   │   ├── postgresql.conf.j2
│   │   └── pg_hba.conf.j2
│   ├── valkey/
│   │   └── valkey.conf.j2
│   ├── netbox/
│   │   ├── configuration.py.j2
│   │   └── gunicorn_config.py.j2
│   └── nginx/
│       ├── netbox.conf.j2
│       └── ssl.conf.j2
├── files/                         # Static files
│   └── systemd/
│       ├── netbox.service
│       └── netbox-rq.service
└── docs/
    ├── ARCHITECTURE.md
    ├── ANSIBLE_DESIGN.md
    └── COMMAND_REFERENCE.md
```

## Design Principles

### 1. Idempotency
All tasks must be idempotent - running multiple times produces same result without side effects.

### 2. Modularity
Each role handles a specific component, enabling independent testing and reuse.

### 3. Separation of Concerns
- **Roles**: Define HOW to configure something
- **Variables**: Define WHAT to configure
- **Inventory**: Define WHERE to configure

### 4. Declarative Configuration
Describe desired state, let Ansible handle implementation details.

### 5. Security First
- Secrets encrypted with Ansible Vault
- Principle of least privilege
- Network segmentation enforced
- No hardcoded credentials

## Role Design

### Role: proxmox_host

**Purpose**: Prepare Proxmox VE host for container deployment

**Tasks**:
- Install required packages (bridge-utils, python3-proxmoxer)
- Configure kernel parameters (ip_forward, overcommit_memory)
- Enable required kernel modules
- Configure firewall base rules
- Set up NAT/masquerading

**Variables**:
```yaml
proxmox_host_packages:
  - bridge-utils
  - python3-proxmoxer
  - python3-requests

proxmox_sysctl_config:
  - name: net.ipv4.ip_forward
    value: 1
  - name: vm.overcommit_memory
    value: 1
```

### Role: proxmox_network

**Purpose**: Create and configure network bridges

**Tasks**:
- Create vmbr1 (backend network)
- Create vmbr2 (DMZ network)
- Configure IP addresses on bridges
- Set up NAT rules for internet access
- Verify bridge connectivity

**Variables**:
```yaml
proxmox_bridges:
  - name: vmbr1
    ip: 10.100.0.1/24
    comment: "Backend network (DB/Cache)"
  - name: vmbr2
    ip: 10.100.1.1/24
    comment: "DMZ network (Application)"

proxmox_nat_networks:
  - 10.100.0.0/24
  - 10.100.1.0/24
```

### Role: proxmox_container

**Purpose**: Generic LXC container creation and management

**Tasks**:
- Download container template if needed
- Create container with specified parameters
- Configure network interfaces
- Set container options (nesting, features)
- Start container
- Wait for container to be ready

**Variables** (per container):
```yaml
container:
  vmid: 100
  hostname: netbox
  template: debian-13-standard_13.1-2_amd64.tar.zst
  ostype: unmanaged
  cores: 2
  memory: 4096
  swap: 2048
  rootfs:
    storage: local-zfs
    size: 32
  networks:
    - name: eth0
      bridge: vmbr1
      ip: 10.100.0.10/24
      gw: 10.100.0.1
    - name: eth1
      bridge: vmbr2
      ip: 10.100.1.10/24
  features:
    - nesting=1
  onboot: true
  unprivileged: true
```

### Role: debian_base

**Purpose**: Configure baseline Debian container settings

**Tasks**:
- Configure /etc/network/interfaces
- Set up DNS resolution
- Configure locales
- Update package cache
- Install common utilities
- Configure systemd settings

**Variables**:
```yaml
debian_base_packages:
  - curl
  - wget
  - vim
  - htop
  - net-tools
  - dnsutils

debian_locales:
  - en_US.UTF-8
```

### Role: postgresql

**Purpose**: Install and configure PostgreSQL database

**Tasks**:
- Install PostgreSQL 17 packages
- Configure postgresql.conf (listen_addresses, shared_buffers, etc.)
- Configure pg_hba.conf (network access rules)
- Create database and user
- Grant privileges
- Start and enable service
- Verify connectivity

**Variables**:
```yaml
postgresql_version: 17
postgresql_listen_addresses: '*'
postgresql_max_connections: 100
postgresql_shared_buffers: '1GB'
postgresql_effective_cache_size: '3GB'

postgresql_databases:
  - name: netbox
    owner: netbox

postgresql_users:
  - name: netbox
    password: "{{ vault_postgresql_password }}"
    role_attr_flags: CREATEDB

postgresql_hba_entries:
  - type: host
    database: all
    user: all
    address: 10.100.0.0/24
    method: scram-sha-256
```

### Role: valkey

**Purpose**: Install and configure Valkey cache server

**Tasks**:
- Install Valkey packages
- Configure locales (fix locale error)
- Create runtime directories
- Template valkey.conf
- Create systemd service override
- Start and enable service
- Verify connectivity

**Variables**:
```yaml
valkey_bind_address: 0.0.0.0
valkey_port: 6379
valkey_protected_mode: false
valkey_maxmemory: 768mb
valkey_maxmemory_policy: allkeys-lru
valkey_databases: 16

valkey_save_intervals:
  - "900 1"
  - "300 10"
  - "60 10000"
```

### Role: netbox_app

**Purpose**: Install and configure NetBox application

**Tasks**:
- Install Python and build dependencies
- Clone NetBox repository (specific version/branch)
- Create Python virtual environment
- Install NetBox requirements
- Install NetBox plugins
- Template configuration.py
- Generate secret key
- Run database migrations
- Create superuser (with vault password)
- Collect static files
- Create systemd service
- Start and enable service
- Verify application

**Variables**:
```yaml
netbox_version: main  # or specific tag
netbox_install_path: /opt/netbox
netbox_user: root

netbox_database:
  host: 10.100.0.20
  port: 5432
  name: netbox
  user: netbox
  password: "{{ vault_postgresql_password }}"

netbox_redis:
  tasks:
    host: 10.100.0.30
    port: 6379
    database: 0
  caching:
    host: 10.100.0.30
    port: 6379
    database: 1

netbox_allowed_hosts:
  - '*'

netbox_plugins:
  - netbox-plugin-dns
  - netbox-secrets==2.4.1
  - netbox-acls
  - netbox-bgp
  - netbox-inventory
  - netbox-floorplan-plugin
  - netbox-reorder-rack

netbox_superuser:
  username: admin
  email: admin@localhost
  password: "{{ vault_netbox_admin_password }}"

gunicorn_bind: 10.100.1.10:8000
gunicorn_workers: 4
gunicorn_timeout: 120
```

### Role: nginx_proxy

**Purpose**: Install and configure Nginx reverse proxy

**Tasks**:
- Install Nginx
- Generate self-signed SSL certificate
- Template Nginx site configuration
- Enable site configuration
- Configure SSL parameters
- Start and enable service
- Verify proxy functionality

**Variables**:
```yaml
nginx_server_name: netbox.example.com
nginx_ssl_cert_path: /etc/nginx/ssl/netbox.crt
nginx_ssl_key_path: /etc/nginx/ssl/netbox.key

nginx_upstream:
  name: netbox
  servers:
    - 10.100.1.10:8000

nginx_proxy_settings:
  proxy_set_header_host: $host
  proxy_set_header_x_real_ip: $remote_addr
  proxy_set_header_x_forwarded_for: $proxy_add_x_forwarded_for
  proxy_set_header_x_forwarded_proto: $scheme
```

## Playbook Execution Flow

### Master Playbook (site.yml)

```yaml
---
- name: Deploy NetBox on Proxmox VE 9.0
  hosts: localhost
  gather_facts: yes
  become: yes

  pre_tasks:
    - name: Verify Proxmox VE version
      shell: pveversion | grep 'pve-manager'
      register: pve_version
      failed_when: "'9.' not in pve_version.stdout"

    - name: Load encrypted variables
      include_vars: group_vars/all/vault.yml

  roles:
    - role: proxmox_host
      tags: [proxmox, host]
    
    - role: proxmox_network
      tags: [proxmox, network]

  tasks:
    - name: Create containers
      include_tasks: playbooks/03-containers-create.yml
      tags: [containers]

- name: Configure database container
  hosts: ct101
  gather_facts: yes
  become: yes
  roles:
    - role: debian_base
    - role: postgresql
  tags: [database]

- name: Configure cache container
  hosts: ct102
  gather_facts: yes
  become: yes
  roles:
    - role: debian_base
    - role: valkey
  tags: [cache]

- name: Configure NetBox container
  hosts: ct100
  gather_facts: yes
  become: yes
  roles:
    - role: debian_base
    - role: netbox_app
  tags: [netbox]

- name: Configure proxy container
  hosts: ct103
  gather_facts: yes
  become: yes
  roles:
    - role: debian_base
    - role: nginx_proxy
  tags: [proxy]

  post_tasks:
    - name: Verify deployment
      include_tasks: playbooks/verify.yml
      tags: [verify]
```

## Variable Hierarchy

### Precedence (highest to lowest):
1. Extra vars (`-e` flag)
2. Task vars
3. Block vars
4. Role vars
5. Play vars
6. Host vars
7. Group vars (inventory)
8. Group vars (group_vars/)
9. Defaults (role defaults)

### Variable Organization

**group_vars/all/network.yml**:
```yaml
---
backend_network:
  cidr: 10.100.0.0/24
  gateway: 10.100.0.1
  bridge: vmbr1

dmz_network:
  cidr: 10.100.1.0/24
  gateway: 10.100.1.1
  bridge: vmbr2

external_network:
  bridge: vmbr0
  dhcp: true
```

**group_vars/all/containers.yml**:
```yaml
---
containers:
  netbox:
    vmid: 100
    hostname: netbox
    cores: 2
    memory: 4096
    swap: 2048
    rootfs_size: 32
    networks:
      - name: eth0
        ip: "{{ backend_network.cidr | ipaddr('10') | ipaddr('address') }}"
        gateway: "{{ backend_network.gateway }}"
        bridge: "{{ backend_network.bridge }}"
      - name: eth1
        ip: "{{ dmz_network.cidr | ipaddr('10') | ipaddr('address') }}"
        bridge: "{{ dmz_network.bridge }}"

  database:
    vmid: 101
    hostname: netbox-db
    cores: 2
    memory: 2048
    swap: 1024
    rootfs_size: 16
    networks:
      - name: eth0
        ip: "{{ backend_network.cidr | ipaddr('20') | ipaddr('address') }}"
        gateway: "{{ backend_network.gateway }}"
        bridge: "{{ backend_network.bridge }}"

  cache:
    vmid: 102
    hostname: netbox-redis
    cores: 1
    memory: 1024
    swap: 512
    rootfs_size: 8
    networks:
      - name: eth0
        ip: "{{ backend_network.cidr | ipaddr('30') | ipaddr('address') }}"
        gateway: "{{ backend_network.gateway }}"
        bridge: "{{ backend_network.bridge }}"

  proxy:
    vmid: 103
    hostname: netbox-proxy
    cores: 1
    memory: 512
    swap: 256
    rootfs_size: 8
    networks:
      - name: eth0
        dhcp: true
        bridge: "{{ external_network.bridge }}"
      - name: eth1
        ip: "{{ dmz_network.cidr | ipaddr('40') | ipaddr('address') }}"
        bridge: "{{ dmz_network.bridge }}"
```

**group_vars/all/vault.yml** (encrypted):
```yaml
---
vault_postgresql_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...encrypted...

vault_netbox_admin_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...encrypted...

vault_netbox_secret_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...encrypted...
```

## Tags Strategy

### Tag Categories:

**Component Tags**:
- `proxmox` - All Proxmox host tasks
- `network` - Network configuration
- `containers` - Container creation
- `database` - PostgreSQL setup
- `cache` - Valkey setup
- `netbox` - NetBox application
- `proxy` - Nginx proxy

**Lifecycle Tags**:
- `install` - Installation tasks
- `configure` - Configuration tasks
- `service` - Service management
- `verify` - Verification tasks

**Usage Examples**:
```bash
# Full deployment
ansible-playbook site.yml

# Only network setup
ansible-playbook site.yml --tags network

# Skip proxy configuration
ansible-playbook site.yml --skip-tags proxy

# Only install packages, skip configuration
ansible-playbook site.yml --tags install

# Configure and restart services
ansible-playbook site.yml --tags configure,service
```

## Error Handling Strategy

### Validation Tasks

Before destructive operations:
```yaml
- name: Check if container already exists
  command: pct status {{ container.vmid }}
  register: container_status
  failed_when: false
  changed_when: false

- name: Fail if container exists and force not set
  fail:
    msg: "Container {{ container.vmid }} already exists. Use -e force=yes to recreate."
  when:
    - container_status.rc == 0
    - force is not defined or not force
```

### Rescue Blocks

For critical operations:
```yaml
- name: Configure PostgreSQL
  block:
    - name: Template postgresql.conf
      template:
        src: postgresql.conf.j2
        dest: /etc/postgresql/17/main/postgresql.conf
      notify: restart postgresql

    - name: Template pg_hba.conf
      template:
        src: pg_hba.conf.j2
        dest: /etc/postgresql/17/main/pg_hba.conf
      notify: restart postgresql

  rescue:
    - name: Restore original configuration
      command: cp /etc/postgresql/17/main/postgresql.conf.bak /etc/postgresql/17/main/postgresql.conf

    - name: Fail with message
      fail:
        msg: "PostgreSQL configuration failed. Original config restored."
```

### Health Checks

After deployments:
```yaml
- name: Wait for PostgreSQL to be ready
  wait_for:
    host: "{{ postgresql_host }}"
    port: 5432
    state: started
    timeout: 30

- name: Verify database connectivity
  postgresql_ping:
    login_host: "{{ postgresql_host }}"
    login_user: "{{ postgresql_user }}"
    login_password: "{{ postgresql_password }}"
  register: db_ping
  retries: 5
  delay: 5
  until: db_ping is succeeded
```

## Testing Strategy

### Molecule Testing

Each role includes Molecule tests:

```yaml
# roles/postgresql/molecule/default/molecule.yml
---
dependency:
  name: galaxy
driver:
  name: docker
platforms:
  - name: postgresql-test
    image: debian:13
    privileged: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
provisioner:
  name: ansible
  playbooks:
    converge: converge.yml
    verify: verify.yml
verifier:
  name: ansible
```

### Integration Tests

Full stack tests in `tests/` directory:
```yaml
- name: Integration test - Full deployment
  hosts: localhost
  tasks:
    - name: Deploy full stack
      include_role:
        name: "{{ item }}"
      loop:
        - proxmox_host
        - proxmox_network
        - proxmox_container
        - postgresql
        - valkey
        - netbox_app
        - nginx_proxy

    - name: Verify NetBox web interface
      uri:
        url: https://localhost
        validate_certs: no
      register: web_check
      failed_when: web_check.status != 200
```

## CI/CD Integration

### GitLab CI Example

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - deploy

lint:
  stage: lint
  script:
    - ansible-lint playbooks/
    - yamllint .

test:
  stage: test
  script:
    - molecule test --all

deploy_staging:
  stage: deploy
  environment: staging
  script:
    - ansible-playbook -i inventory/staging site.yml
  only:
    - develop

deploy_production:
  stage: deploy
  environment: production
  script:
    - ansible-playbook -i inventory/production site.yml
  only:
    - main
  when: manual
```

## Best Practices

### 1. Vault Management

```bash
# Create vault password file
echo "your-vault-password" > ~/.vault_pass

# Encrypt secrets
ansible-vault encrypt group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# Edit encrypted file
ansible-vault edit group_vars/all/vault.yml --vault-password-file ~/.vault_pass

# Run playbook with vault
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

### 2. Dry Run Testing

```bash
# Check mode (no changes)
ansible-playbook site.yml --check

# Diff mode (show changes)
ansible-playbook site.yml --check --diff

# Limit to specific hosts
ansible-playbook site.yml --limit ct100
```

### 3. Documentation

- Document all variables in `defaults/main.yml`
- Include examples in `README.md` for each role
- Maintain CHANGELOG.md for tracking changes
- Use comments for complex logic

### 4. Version Control

```
.gitignore:
*.retry
.vault_pass
*.log
.molecule/
```

### 5. Code Quality

- Use `ansible-lint` for style checking
- Follow Ansible best practices guide
- Keep roles under 500 lines
- Use handlers for service restarts
- Avoid `shell` module when alternatives exist

## Performance Optimization

### 1. Fact Caching

```ini
# ansible.cfg
[defaults]
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 3600
```

### 2. Pipelining

```ini
[ssh_connection]
pipelining = True
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
```

### 3. Parallel Execution

```ini
[defaults]
forks = 10
```

```bash
# Increase parallelism for specific playbook
ansible-playbook site.yml --forks 20
```

### 4. Strategic Task Ordering

- Download templates early (parallel)
- Group similar tasks (reduce context switching)
- Use async for long-running tasks

```yaml
- name: Download container templates
  async: 300
  poll: 0
  register: template_download
  loop: "{{ container_templates }}"

- name: Wait for downloads
  async_status:
    jid: "{{ item.ansible_job_id }}"
  register: template_jobs
  until: template_jobs.finished
  retries: 30
  loop: "{{ template_download.results }}"
```

## Conclusion

This Ansible project provides a fully automated, idempotent deployment of NetBox on Proxmox VE 9.0. The modular design allows for easy customization, testing, and maintenance while following infrastructure-as-code best practices.
