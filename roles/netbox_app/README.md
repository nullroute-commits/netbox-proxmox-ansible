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

## Security Notes

- `netbox_app_allowed_hosts: ["*"]` is safe when behind a reverse proxy
- Store passwords in Ansible Vault

## License

MIT

## Author

NetBox Proxmox Team
