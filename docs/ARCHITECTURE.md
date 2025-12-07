# NetBox on Proxmox VE 9.1 - Architecture Documentation

## Overview

This document describes the architecture, design decisions, and implementation details for deploying NetBox in a multi-container LXC environment on Proxmox VE 9.1+.

**System Information Collection:** Use [automation_nation.git](https://github.com/nullroute-commits/automation_nation.git) bash script to collect comprehensive hardware and software information from your Proxmox node before deployment.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  Proxmox VE 9.1+ Host                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    vmbr0 (External)                         │ │
│  │                  Physical Bridge                            │ │
│  │                      ↓                                       │ │
│  │            ┌─────────────────┐                              │ │
│  │            │   CT 103        │                              │ │
│  │            │  netbox-proxy   │                              │ │
│  │            │  Nginx          │                              │ │
│  │            │  eth0: DHCP     │                              │ │
│  │            └────────┬────────┘                              │ │
│  └─────────────────────┼──────────────────────────────────────┘ │
│                        │                                         │
│  ┌────────────────────┼──────────────────────────────────────┐ │
│  │                vmbr2 (DMZ - 10.100.1.0/24)                 │ │
│  │                    │                                         │ │
│  │         ┌──────────┴────────┐                               │ │
│  │         │                   │                               │ │
│  │  ┌──────▼──────┐   ┌───────▼──────┐                        │ │
│  │  │   CT 103    │   │   CT 100     │                        │ │
│  │  │ eth1: .40   │   │   netbox     │                        │ │
│  │  └─────────────┘   │ eth1: .10    │                        │ │
│  │                    └──────┬───────┘                         │ │
│  └───────────────────────────┼──────────────────────────────┘ │
│                               │                                 │
│  ┌───────────────────────────┼──────────────────────────────┐ │
│  │             vmbr1 (Backend - 10.100.0.0/24)               │ │
│  │                           │                                 │ │
│  │                    ┌──────┴─────┐                          │ │
│  │                    │            │                          │ │
│  │         ┌──────────▼─┐   ┌─────▼──────┐  ┌──────────┐    │ │
│  │         │  CT 100     │   │  CT 101    │  │  CT 102  │    │ │
│  │         │ eth0: .10   │   │ netbox-db  │  │  redis   │    │ │
│  │         │ (NetBox)    │   │ eth0: .20  │  │eth0: .30 │    │ │
│  │         └─────────────┘   └────────────┘  └──────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

## Network Design

### Three-Tier Network Segmentation

#### Tier 1: External Network (vmbr0)
- **Purpose**: Public-facing internet access
- **Connected Containers**: CT 103 (netbox-proxy) only
- **Security**: Only reverse proxy exposed to external traffic
- **Configuration**: Physical bridge connected to host network interface

#### Tier 2: DMZ Network (vmbr2 - 10.100.1.0/24)
- **Purpose**: Application tier isolation
- **Connected Containers**: 
  - CT 103 (netbox-proxy): 10.100.1.40/24
  - CT 100 (netbox): 10.100.1.10/24
- **Security**: Application servers isolated from direct internet access
- **Gateway**: 10.100.1.1 (Proxmox host)

#### Tier 3: Backend Network (vmbr1 - 10.100.0.0/24)
- **Purpose**: Database and cache layer isolation
- **Connected Containers**:
  - CT 100 (netbox): 10.100.0.10/24
  - CT 101 (netbox-db): 10.100.0.20/24
  - CT 102 (netbox-redis): 10.100.0.30/24
- **Security**: No external access, backend services only
- **Gateway**: 10.100.0.1 (Proxmox host)

### Network Security Features

1. **Network Isolation**: Each tier operates independently
2. **NAT/Masquerading**: Backend networks use NAT for package updates
3. **No Direct Access**: Database and cache not accessible from external network
4. **Firewall Ready**: iptables rules configured on host for additional security

## Container Architecture

### CT 100: NetBox Application Server
- **OS**: Debian 13 (Trixie)
- **vCPUs**: 2 cores
- **Memory**: 4096 MB RAM, 2048 MB swap
- **Storage**: 32 GB (local-zfs)
- **Network**: Dual-homed (vmbr1 + vmbr2)
- **Services**:
  - NetBox (latest from GitHub main branch)
  - Gunicorn WSGI server (4 workers)
  - Python 3.13 virtualenv
- **Features**: Unprivileged container with nesting enabled

### CT 101: PostgreSQL Database Server
- **OS**: Debian 13 (Trixie)
- **vCPUs**: 2 cores
- **Memory**: 2048 MB RAM, 1024 MB swap
- **Storage**: 16 GB (local-zfs)
- **Network**: Backend only (vmbr1)
- **Services**:
  - PostgreSQL 17.6
  - Database: netbox
  - User: netbox (with full privileges)
- **Configuration**:
  - Listen address: 0.0.0.0 (all interfaces)
  - Authentication: scram-sha-256
  - Network access: 10.100.0.0/24 subnet only

### CT 102: Valkey Cache Server
- **OS**: Debian 13 (Trixie)
- **vCPUs**: 1 core
- **Memory**: 1024 MB RAM, 512 MB swap
- **Storage**: 8 GB (local-zfs)
- **Network**: Backend only (vmbr1)
- **Services**:
  - Valkey 8.1.1 (Redis-compatible fork)
  - Port: 6379
  - Two databases: tasks (0) and caching (1)
- **Configuration**:
  - Bind address: 0.0.0.0
  - Protected mode: disabled (internal network only)
  - Persistence: RDB snapshots

### CT 103: Nginx Reverse Proxy
- **OS**: Debian 13 (Trixie)
- **vCPUs**: 1 core
- **Memory**: 512 MB RAM, 256 MB swap
- **Storage**: 8 GB (local-zfs)
- **Network**: Dual-homed (vmbr0 + vmbr2)
- **Services**:
  - Nginx (latest stable)
  - SSL/TLS termination
  - Reverse proxy to NetBox
- **Configuration**:
  - Frontend: eth0 (DHCP on vmbr0)
  - Backend: eth1 (10.100.1.40/24 on vmbr2)

## Technology Stack

### Core Components

All versions pinned to stable releases as of December 2025. See [VERSIONS.md](../VERSIONS.md) for complete version details.

| Component | Version | Purpose | Support Until |
|-----------|---------|---------|---------------|
| Proxmox VE | 9.0.3 | Virtualization platform | - |
| Debian | 13.1 (Trixie) | Container OS | - |
| NetBox | v4.4.7 | IPAM/DCIM application | - |
| PostgreSQL | 17.6 | Primary database | November 2029 |
| Valkey | 8.1.1 | Caching and task queue | - |
| Gunicorn | 23.0.0 | WSGI HTTP server | - |
| Nginx | 1.26.3 | Reverse proxy | - |
| Python | 3.13.5 | Application runtime | October 2029 |

### NetBox Plugins

All plugins pinned to latest stable versions as of December 2025:

1. **netbox-plugin-dns** (v1.4.4) - DNS zone and record management
2. **netbox-secrets** (v2.4.1) - Encrypted secret storage (Onemind-Services-LLC)
3. **netbox-acls** (v1.9.1) - Access control lists
4. **netbox-bgp** (v0.17.0) - BGP peering management
5. **netbox-inventory** (v2.4.1) - Enhanced inventory tracking
6. **netbox-floorplan-plugin** (v0.8.0) - Datacenter floor planning
7. **netbox-reorder-rack** (v1.1.4) - Rack device reordering

**Version Compatibility:**
- All plugins compatible with NetBox v4.4.7
- Tested and verified working
- See [VERSIONS.md](../VERSIONS.md) for update policies

## Design Decisions

### Why LXC Containers Instead of VMs?

1. **Resource Efficiency**: Containers share kernel, reducing overhead
2. **Faster Deployment**: Seconds vs minutes for startup
3. **Better Density**: More containers per host than VMs
4. **Easier Management**: Simple `pct` commands for lifecycle
5. **Sufficient Isolation**: Application-level separation adequate for this use case

### Why Three-Tier Network Design?

1. **Defense in Depth**: Multiple security boundaries
2. **Blast Radius Containment**: Compromise doesn't expose everything
3. **Principle of Least Privilege**: Services only access what they need
4. **Compliance**: Aligns with security frameworks (PCI-DSS, NIST)
5. **Scalability**: Easy to add more application or database servers

### Why Debian 13 (Trixie)?

1. **Latest Packages**: Most current versions of dependencies
2. **PostgreSQL 17**: Latest stable database features
3. **Python 3.13**: Modern Python with performance improvements
4. **Long Support**: Debian's stable support cycle
5. **Known Quantity**: Well-tested in production environments

### Why Valkey Over Redis?

1. **Open Source**: True FOSS without license restrictions
2. **Compatibility**: Drop-in replacement for Redis
3. **Active Development**: Community-driven improvements
4. **NetBox Compatibility**: Official Docker compose uses Valkey
5. **Performance**: Optimized fork with better defaults

### Why Separate Database Container?

1. **Resource Isolation**: Database has dedicated resources
2. **Security**: Limited network exposure
3. **Backup Simplicity**: Database snapshots independent of app
4. **Scaling**: Can upgrade database separately
5. **Troubleshooting**: Isolated logs and metrics

### Why Nginx as Reverse Proxy?

1. **Performance**: Efficient static file serving
2. **SSL Termination**: Centralized certificate management
3. **Load Balancing**: Can distribute to multiple NetBox backends
4. **Caching**: Optional static content caching
5. **Security**: Additional layer for rate limiting, filtering

## Storage Strategy

### ZFS Backend (local-zfs)

**Advantages**:
- **Snapshots**: Instant container snapshots for backups
- **Clones**: Fast container cloning for testing
- **Compression**: Transparent LZ4 compression saves space
- **Data Integrity**: Checksumming prevents silent corruption
- **Performance**: ARC caching improves read performance

**Implementation**:
- All container root filesystems on ZFS zvols
- Automatic snapshots recommended (via `pve-zsync` or custom)
- Consider separate dataset for PostgreSQL data with tuned recordsize

## Security Considerations

### Network Security

1. **Firewall Rules**: iptables FORWARD rules control inter-network traffic
2. **NAT Masquerading**: Backend networks masqueraded for updates only
3. **No Port Forwarding**: External access only via Nginx proxy
4. **PostgreSQL**: Authentication required, network ACLs enforced
5. **Valkey**: No authentication (internal network trust boundary)

### Container Security

1. **Unprivileged Containers**: All containers run unprivileged
2. **AppArmor**: Container-specific AppArmor profiles
3. **Capabilities**: Limited Linux capabilities
4. **No Nesting**: Except CT 100 (needed for some NetBox features)
5. **Root Filesystem**: Read-only where possible

### Application Security

1. **Secret Key**: Strong random secret generated for Django
2. **Database Passwords**: Strong passwords, scram-sha-256 auth
3. **SSL/TLS**: Self-signed certificates (production should use Let's Encrypt)
4. **Django Security**: DEBUG=False, ALLOWED_HOSTS restricted
5. **Plugin Vetting**: All plugins from trusted sources

## High Availability Considerations

### Current Single-Node Limitations

This deployment is single-node and has several SPOFs:

1. **Proxmox Host**: Hardware failure impacts all services
2. **Database**: Single PostgreSQL instance
3. **Application**: Single NetBox container
4. **Network**: No redundant paths

### Future HA Enhancements

1. **Proxmox Cluster**:
   - Add 2+ nodes for quorum
   - Enable HA for containers
   - Shared storage (Ceph) for live migration

2. **Database HA**:
   - PostgreSQL streaming replication
   - Patroni for automatic failover
   - Connection pooling (PgBouncer)

3. **Application Scaling**:
   - Multiple NetBox containers
   - Load balancer (HAProxy or Nginx)
   - Shared storage for media files

4. **Cache Redundancy**:
   - Valkey Sentinel for failover
   - Valkey Cluster for sharding
   - Session persistence to database

## Monitoring and Observability

### Recommended Monitoring Stack

1. **Node Exporter**: Proxmox host metrics
2. **cAdvisor**: Container resource usage
3. **PostgreSQL Exporter**: Database metrics
4. **Redis Exporter**: Valkey metrics (compatible)
5. **Nginx Exporter**: Proxy metrics
6. **NetBox Prometheus**: Built-in metrics endpoint
7. **Grafana**: Unified dashboard

### Key Metrics to Monitor

- **Host**: CPU, memory, disk I/O, network throughput
- **Containers**: CPU usage, memory usage, restart count
- **Database**: Connections, query time, cache hit ratio, replication lag
- **Cache**: Memory usage, hit rate, eviction count
- **Application**: Request rate, response time, error rate, worker utilization
- **Network**: Bandwidth, packet loss, latency between tiers

## Backup Strategy

### What to Backup

1. **PostgreSQL Database**:
   - Daily `pg_dump` to external storage
   - Point-in-time recovery (WAL archiving)
   - Retention: 30 days daily, 12 months monthly

2. **NetBox Configuration**:
   - `/opt/netbox/netbox/netbox/configuration.py`
   - Custom scripts and reports
   - Media files (`/opt/netbox/netbox/media`)

3. **Container Snapshots**:
   - Weekly ZFS snapshots of all containers
   - Retention: 4 weekly snapshots

### Backup Implementation

```bash
# PostgreSQL backup
pct exec 101 -- su - postgres -c 'pg_dump netbox' > netbox_$(date +%Y%m%d).sql

# Container snapshot
pct snapshot 100 backup-$(date +%Y%m%d)

# Replicate to external storage
pve-zsync sync --source <VMID> --dest <remote>
```

## Performance Tuning

### PostgreSQL Tuning

```ini
# /etc/postgresql/17/main/postgresql.conf
shared_buffers = 1GB              # 25% of container RAM
effective_cache_size = 3GB        # 75% of container RAM
work_mem = 16MB                   # Per operation
maintenance_work_mem = 256MB      # Maintenance operations
max_connections = 100             # Connection limit
```

### Gunicorn Tuning

```python
# Workers: 2-4 × CPU cores
workers = 4
worker_class = 'sync'
timeout = 120
max_requests = 1000              # Worker recycling
max_requests_jitter = 100
```

### Valkey Tuning

```conf
# /etc/valkey/valkey.conf
maxmemory 768mb                  # 75% of container RAM
maxmemory-policy allkeys-lru     # Eviction policy
save 900 1                       # RDB persistence
save 300 10
save 60 10000
```

### Network Tuning

```bash
# On Proxmox host
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w vm.overcommit_memory=1  # For Valkey
```

## Disaster Recovery

### Recovery Time Objective (RTO)

- **Database Restore**: 15-30 minutes
- **Application Restore**: 10-15 minutes  
- **Full Stack Restore**: 45-60 minutes

### Recovery Point Objective (RPO)

- **Database**: 24 hours (daily backups)
- **Configuration**: 1 hour (version control)
- **Media Files**: 24 hours (daily sync)

### Recovery Procedures

1. **Database Corruption**:
   ```bash
   pct restore 101 <backup-file>
   pct exec 101 -- psql -U postgres < netbox_backup.sql
   ```

2. **Application Failure**:
   ```bash
   pct restore 100 <backup-file>
   pct start 100
   ```

3. **Complete Proxmox Host Failure**:
   - Rebuild Proxmox on new hardware
   - Restore containers from backup storage
   - Reconfigure network bridges
   - Verify service connectivity

## Maintenance Procedures

### Regular Maintenance Tasks

**Daily**:
- Check service health (systemctl status)
- Review logs for errors
- Monitor disk space

**Weekly**:
- Database vacuum analyze
- Review NetBox task queue
- Check for available updates

**Monthly**:
- Apply security updates
- Review and rotate logs
- Test backup restores
- Database performance analysis

### Update Procedures

1. **NetBox Updates**:
   ```bash
   pct exec 100 -- bash -c 'cd /opt/netbox && git pull'
   pct exec 100 -- bash -c 'source venv/bin/activate && pip install -U -r requirements.txt'
   pct exec 100 -- bash -c 'python manage.py migrate'
   pct exec 100 -- systemctl restart netbox
   ```

2. **System Updates**:
   ```bash
   pct exec <VMID> -- apt update && apt upgrade -y
   # Reboot if kernel updated
   pct reboot <VMID>
   ```

## Troubleshooting Guide

### Common Issues

**1. Network Connectivity Lost After Reboot**
- **Cause**: Network interfaces not configured in `/etc/network/interfaces`
- **Solution**: Recreate interface configs or use `pct set` commands

**2. Valkey Won't Start**
- **Cause**: Locale errors or missing runtime directory
- **Solution**: Create `/run/valkey`, comment out `locale-collate`

**3. PostgreSQL Connection Refused**
- **Cause**: Not listening on network or pg_hba.conf misconfigured
- **Solution**: Check `listen_addresses = '*'` and pg_hba.conf entries

**4. NetBox 500 Errors**
- **Cause**: Database connection, cache unavailable, or migrations needed
- **Solution**: Check logs, verify services, run `migrate`

**5. Nginx 502 Bad Gateway**
- **Cause**: NetBox/Gunicorn not running or wrong upstream address
- **Solution**: Check NetBox service, verify listen address

### Debug Commands

```bash
# Check container status
pct list

# View container logs
pct exec <VMID> -- journalctl -xe

# Test network connectivity
pct exec 100 -- ping 10.100.0.20
pct exec 100 -- telnet 10.100.0.20 5432

# Check service status
pct exec 100 -- systemctl status netbox
pct exec 101 -- systemctl status postgresql
pct exec 102 -- ps aux | grep valkey

# View application logs
pct exec 100 -- tail -f /var/log/syslog
pct exec 101 -- tail -f /var/log/postgresql/postgresql-17-main.log
```

## Conclusion

This architecture provides a secure, scalable, and maintainable NetBox deployment on Proxmox VE 9.0. The three-tier network design ensures proper security boundaries, while containerization provides resource efficiency and management simplicity.

The design can be extended for high availability by adding Proxmox cluster nodes, implementing database replication, and load balancing multiple NetBox instances.
