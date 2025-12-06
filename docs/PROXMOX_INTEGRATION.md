# Proxmox VE Integration Guide (Proxbox)

This guide covers the setup and configuration of the NetBox-Proxbox integration plugin, which enables automatic synchronization of Proxmox VE infrastructure data with NetBox.

## Overview

The `netbox-proxbox` plugin (v0.0.6b2.post1) by netdevopsbr provides:

- **Cluster Discovery**: Automatic discovery of Proxmox clusters
- **Node Synchronization**: Import Proxmox nodes as NetBox devices
- **VM Import**: Synchronize virtual machines to NetBox
- **Container Import**: Synchronize LXC containers to NetBox
- **Storage Tracking**: Import storage resources and pools
- **UI Management**: Web-based configuration and sync control

## Prerequisites

### Proxmox VE Requirements

- Proxmox VE 8.3 or later (8.x/9.x)
- API access enabled (default port 8006)
- Dedicated API user with appropriate permissions

### NetBox Requirements

- NetBox 4.2.6 or later (4.4.7 recommended)
- Plugin installed and enabled
- Network access to Proxmox API

## Proxmox API User Setup

### Option 1: Password Authentication

```bash
# Connect to Proxmox host
ssh root@proxmox-host

# Create role with minimum required permissions
pveum role add NetBoxSync -privs "VM.Audit,VM.Monitor,Datastore.Audit,SDN.Audit,Sys.Audit,Pool.Audit"

# Create dedicated user
pveum user add netbox@pve -comment "NetBox Proxbox Integration User"

# Assign role to user at datacenter level
pveum acl modify / -user netbox@pve -role NetBoxSync

# Set password
pveum passwd netbox@pve
# Enter secure password when prompted
```

### Option 2: API Token Authentication (Recommended)

```bash
# Create user first (if not exists)
pveum user add netbox@pve -comment "NetBox Proxbox Integration User"

# Create API token
pveum user token add netbox@pve netbox-token -privsep=0

# Note the token ID and secret - they cannot be retrieved later!
# Format: netbox@pve!netbox-token=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Assign role
pveum acl modify / -user netbox@pve -role NetBoxSync
```

### Permission Details

| Permission | Purpose |
|------------|---------|
| `VM.Audit` | View VM configuration and status |
| `VM.Monitor` | Access VM monitoring data |
| `Datastore.Audit` | View storage configuration |
| `SDN.Audit` | View network configuration |
| `Sys.Audit` | View system information |
| `Pool.Audit` | View resource pool configuration |

## NetBox Plugin Configuration

### Ansible Variables

The plugin is configured via Ansible variables in `roles/netbox_app/defaults/main.yml`:

```yaml
# Enable/disable the plugin
netbox_app_proxbox_plugin_enabled: true

# Plugin configuration (Proxbox settings are configured via NetBox UI)
netbox_app_proxbox_config:
  default_settings:
    verify_ssl: true
    timeout: 30
```

### Vault Credentials

Store Proxmox API credentials securely in Ansible Vault:

```yaml
# group_vars/all/vault.yml
vault_proxmox_api_user: "netbox@pve"
vault_proxmox_api_password: "your-secure-password"

# Or for token authentication:
vault_proxmox_api_token_id: "netbox@pve!netbox-token"
vault_proxmox_api_token_secret: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

Encrypt the vault file:

```bash
ansible-vault encrypt group_vars/all/vault.yml
```

## Network Configuration

### Required Connectivity

The NetBox container (CT 100) needs network access to the Proxmox API:

```
NetBox Container (10.100.0.10) → Proxmox API (proxmox-host:8006)
```

### Option A: Via Backend Network Gateway

If your Proxmox host is the gateway for the backend network:

1. NetBox connects to gateway IP (10.100.0.1:8006)
2. No additional firewall rules needed

### Option B: Direct Connection

If Proxmox API is on a different host:

```bash
# On Proxmox host, allow NetBox container access
iptables -A INPUT -s 10.100.0.10 -p tcp --dport 8006 -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Testing Connectivity

From the Proxmox host, test API access from NetBox container:

```bash
# Test basic connectivity
pct exec 100 -- curl -k https://10.100.0.1:8006/api2/json/version

# Test authentication (password)
pct exec 100 -- curl -k -d 'username=netbox@pve&password=YOUR_PASSWORD' \
  https://10.100.0.1:8006/api2/json/access/ticket

# Test authentication (token)
pct exec 100 -- curl -k -H "Authorization: PVEAPIToken=netbox@pve!netbox-token=TOKEN_SECRET" \
  https://10.100.0.1:8006/api2/json/version
```

## Initial Setup in NetBox

After deployment, configure the Proxmox connection in NetBox:

1. **Log in to NetBox** as admin user

2. **Navigate to Plugins** → **Proxbox**

3. **Add Proxmox Cluster**:
   - Name: `primary-cluster`
   - Host: `10.100.0.1` (or your Proxmox host IP)
   - Port: `8006`
   - Username: `netbox@pve`
   - Password/Token: (your credentials)
   - Verify SSL: Enable for production

4. **Test Connection** using the "Test" button

5. **Run Initial Sync** to import infrastructure data

## Synchronization Features

### What Gets Synchronized

| Proxmox Object | NetBox Object | Notes |
|----------------|---------------|-------|
| Cluster | Cluster Group | Organizational grouping |
| Node | Device | Hypervisor server |
| VM | Virtual Machine | Full VM configuration |
| LXC Container | Virtual Machine | Marked as container |
| Storage Pool | Storage | Datastore mapping |
| Network Bridge | Interface | Network configuration |

### Sync Modes

1. **Full Sync**: Complete infrastructure import
2. **Incremental Sync**: Only changed objects
3. **Read-Only Mode**: Import only, no NetBox modifications

### Scheduling Syncs

Configure automated synchronization via the Proxbox plugin UI or using NetBox scheduled jobs.

## Troubleshooting

### Connection Refused

```
Error: Connection refused to proxmox-host:8006
```

**Solution:**
1. Verify Proxmox API is running: `systemctl status pveproxy`
2. Check firewall rules allow port 8006
3. Test connectivity with curl

### SSL Certificate Errors

```
Error: SSL certificate verification failed
```

**Solutions:**
1. Use `verify_ssl: false` for self-signed certificates (development only)
2. Add Proxmox CA to container trust store:
   ```bash
   pct exec 100 -- bash -c "wget -O /usr/local/share/ca-certificates/proxmox.crt \
     https://proxmox-host:8006/pve-root-ca.pem && update-ca-certificates"
   ```

### Authentication Failures

```
Error: authentication failure (401)
```

**Solutions:**
1. Verify username format: `user@realm` (e.g., `netbox@pve`)
2. Check password/token is correct
3. Verify user has required permissions

### Plugin Not Loading

```
Error: No module named 'netbox_proxbox'
```

**Solutions:**
1. Verify plugin installation:
   ```bash
   pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && pip list | grep proxbox"
   ```
2. Run migrations:
   ```bash
   pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
     cd /opt/netbox/netbox && python manage.py migrate"
   ```
3. Restart NetBox:
   ```bash
   pct exec 100 -- systemctl restart netbox
   ```

### Sync Errors

Check NetBox logs for detailed error information:

```bash
pct exec 100 -- journalctl -u netbox -f
```

## Security Best Practices

### API Credentials

- Use API tokens instead of passwords
- Store credentials in Ansible Vault
- Use separate tokens per application
- Rotate tokens periodically

### Network Security

- Enable SSL verification in production
- Restrict API access to specific IPs
- Use firewall rules to limit exposure
- Consider VPN for remote access

### Principle of Least Privilege

- Create dedicated API user for NetBox
- Assign minimum required permissions
- Use read-only mode initially
- Audit API access logs

## Maintenance

### Updating the Plugin

```bash
# Update plugin version in role defaults
# Then run playbook to update

# Or manually update:
pct exec 100 -- bash -c "source /opt/netbox/venv/bin/activate && \
  pip install --upgrade netbox-proxbox==X.Y.Z"

# Restart NetBox
pct exec 100 -- systemctl restart netbox
```

### Checking Sync Status

```bash
# View sync logs
pct exec 100 -- journalctl -u netbox | grep -i proxbox

# Check last sync time in NetBox UI
# Navigate to Plugins → Proxbox → Sync Status
```

### Clearing Sync Data

If you need to re-sync from scratch:

1. Delete imported objects in NetBox
2. Clear sync state in plugin settings
3. Run fresh full sync

---

**Document Version:** 1.1
**Last Updated:** December 2025
**Plugin Version:** netbox-proxbox 0.0.6b2.post1
