# Valkey Role

Install and configure Valkey cache server (Redis alternative) for NetBox.

## Requirements

- Proxmox VE 8.x or 9.x
- LXC container with `debian_base` role applied
- Network connectivity to Valkey APT repositories

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `valkey_version` | `8.1.1` | Valkey version |
| `valkey_package` | `valkey` | Package name |
| `valkey_bind_address` | `0.0.0.0` | Bind address |
| `valkey_port` | `6379` | Valkey port |
| `valkey_protected_mode` | `false` | Protected mode setting |
| `valkey_maxmemory` | `768mb` | Maximum memory |
| `valkey_maxmemory_policy` | `allkeys-lru` | Eviction policy |
| `valkey_databases` | `16` | Number of databases |
| `valkey_repo_key_url` | See defaults | Repository GPG key URL |
| `valkey_repo_keyring` | See defaults | Keyring path |
| `valkey_repo_url` | See defaults | Repository URL |
| `valkey_repo_distribution` | `bookworm` | Repository distribution |

## Handlers

| Handler | Description |
|---------|-------------|
| `valkey_restart` | Restart Valkey service |
| `valkey_reload` | Reload Valkey configuration |

## Dependencies

- `debian_base`

## Example Playbook

```yaml
- hosts: cache
  roles:
    - role: valkey
      vars:
        container:
          vmid: 102
```

## Security Notes

- `valkey_protected_mode: false` is acceptable when Valkey is on an isolated backend network
- Consider enabling authentication for production environments

## License

MIT

## Author

NetBox Proxmox Team
