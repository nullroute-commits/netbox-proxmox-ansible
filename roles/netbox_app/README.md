# NetBox Application Role

Install and configure NetBox IPAM/DCIM application.

## Requirements

- Proxmox VE 8.x or 9.x
- LXC container with `debian_base` role applied
- PostgreSQL database (from `postgresql` role)
- Valkey cache (from `valkey` role)

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `netbox_app_version` | `v4.4.7` | NetBox version tag |
| `netbox_app_repository` | GitHub URL | NetBox Git repository |
| `netbox_app_install_path` | `/opt/netbox` | Installation path |
| `netbox_app_user` | `netbox` | System user |
| `netbox_app_group` | `netbox` | System group |
| `netbox_app_python_version` | `3.13` | Python version |
| `netbox_app_gunicorn_version` | `23.0.0` | Gunicorn version |
| `netbox_app_gunicorn_bind` | `0.0.0.0:8000` | Gunicorn bind address |
| `netbox_app_gunicorn_workers` | `4` | Number of Gunicorn workers |
| `netbox_app_allowed_hosts` | `["*"]` | Django allowed hosts |
| `netbox_app_superuser_username` | `admin` | Admin username |
| `netbox_app_superuser_email` | `admin@localhost` | Admin email |
| `netbox_app_plugins` | See defaults | List of plugins to install |
| `netbox_app_plugin_modules` | See defaults | Plugin module names |
| `netbox_app_proxbox_plugin_enabled` | `true` | Enable Proxbox plugin |
| `netbox_app_proxbox_config` | See defaults | Proxbox plugin settings |

## Installed Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| netbox-plugin-dns | 1.4.4 | DNS zone/record management |
| netbox-secrets | 2.4.1 | Encrypted secret storage |
| netbox-acls | 1.9.1 | Access control lists |
| netbox-bgp | 0.17.0 | BGP peering management |
| netbox-inventory | 2.4.1 | Enhanced inventory tracking |
| netbox-floorplan-plugin | 0.8.0 | Datacenter floor planning |
| netbox-reorder-rack | 1.1.4 | Rack device reordering |
| netbox-proxbox | 0.0.6b2.post1 | Proxmox VE integration |

## Handlers

| Handler | Description |
|---------|-------------|
| `netbox_restart` | Restart NetBox service |
| `netbox_reload` | Reload NetBox configuration |
| `netbox_rq_restart` | Restart NetBox RQ worker |

## Dependencies

- `debian_base`

## Example Playbook

```yaml
- hosts: netbox
  roles:
    - role: netbox_app
      vars:
        container:
          vmid: 100
        vault_netbox_db_password: "DatabasePassword!"
        vault_netbox_admin_password: "AdminPassword!"
```

## Proxmox Integration (Proxbox)

The Proxbox plugin enables synchronization of Proxmox VE infrastructure:

- Cluster discovery and import
- VM and container synchronization
- Storage resource tracking
- Node device mapping

See [docs/PROXMOX_INTEGRATION.md](../../docs/PROXMOX_INTEGRATION.md) for setup guide.

## Security Notes

- `netbox_app_allowed_hosts: ["*"]` is safe when behind a reverse proxy
- Store passwords in Ansible Vault
- Use API tokens for Proxmox integration

## License

MIT

## Author

NetBox Proxmox Team
