# Proxmox Container Role

Generic LXC container creation and management for Proxmox VE.

## Requirements

- Proxmox VE 8.x or 9.x
- `proxmox_network` role applied
- Container template downloaded

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `proxmox_container_template` | See defaults | Container template |
| `proxmox_container_template_storage` | `local` | Template storage |
| `proxmox_container_storage` | `local-zfs` | Container storage |
| `proxmox_container_ostype` | `unmanaged` | OS type |
| `proxmox_container_unprivileged` | `true` | Unprivileged container |
| `proxmox_container_onboot` | `true` | Start on boot |
| `proxmox_container_default_cores` | `1` | Default CPU cores |
| `proxmox_container_default_memory` | `1024` | Default memory (MB) |
| `proxmox_container_default_swap` | `512` | Default swap (MB) |
| `proxmox_container_default_disk` | `8` | Default disk size (GB) |
| `proxmox_container_wait_timeout` | `30` | Startup wait timeout |

## Handlers

| Handler | Description |
|---------|-------------|
| `container_network_restart` | Restart container networking |

## Dependencies

- `proxmox_network`

## Example Playbook

```yaml
- hosts: proxmox_hosts
  roles:
    - role: proxmox_container
      vars:
        container:
          vmid: 100
          hostname: netbox
          cpu: 2
          memory: 4096
          disk: 32
          backend_ip: 10.100.0.10
```

## License

MIT

## Author

NetBox Proxmox Team
