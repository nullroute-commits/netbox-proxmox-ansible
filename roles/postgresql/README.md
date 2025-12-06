# PostgreSQL Role

Install and configure PostgreSQL database server for NetBox.

## Requirements

- Proxmox VE 8.x or 9.x
- LXC container with `debian_base` role applied
- Network connectivity to PostgreSQL APT repositories

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `postgresql_version` | `17` | PostgreSQL major version |
| `postgresql_full_version` | `17.6` | PostgreSQL full version |
| `postgresql_listen_addresses` | `*` | Listen addresses |
| `postgresql_max_connections` | `200` | Maximum connections |
| `postgresql_port` | `5432` | PostgreSQL port |
| `postgresql_auth_method` | `md5` | Authentication method |
| `postgresql_netbox_database` | `netbox` | NetBox database name |
| `postgresql_netbox_user` | `netbox` | NetBox database user |

## Handlers

| Handler | Description |
|---------|-------------|
| `postgresql_restart` | Restart PostgreSQL service |
| `postgresql_reload` | Reload PostgreSQL configuration |

## Dependencies

- `debian_base`

## Example Playbook

```yaml
- hosts: database
  roles:
    - role: postgresql
      vars:
        container:
          vmid: 101
        vault_netbox_db_password: "SecurePassword123!"
```

## Security Notes

- `postgresql_listen_addresses: "*"` is safe when PostgreSQL is on an isolated backend network
- Ensure `pg_hba.conf` restricts access to trusted networks only

## License

MIT

## Author

NetBox Proxmox Team
