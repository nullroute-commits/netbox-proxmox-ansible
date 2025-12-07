# Proxmox Host Role

Prepare Proxmox VE host for container deployment.

## Requirements

- Proxmox VE 9.0+ (9.1+ recommended)
- Root or sudo access
- Hardware validated using automation_nation.git collect_info.sh

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `proxmox_host_version` | `9.1` | Proxmox VE version (9.0+ supported) |
| `proxmox_host_min_version` | `9.0` | Minimum supported Proxmox version |
| `proxmox_host_packages` | See defaults | Required packages |
| `proxmox_host_sysctl` | See defaults | Sysctl parameters |
| `proxmox_host_log_dir` | `/var/log/ansible` | Log directory |
| `proxmox_host_log_mode` | `0755` | Log directory mode |

## Handlers

| Handler | Description |
|---------|-------------|
| `sysctl_reload` | Reload sysctl configuration |

## Dependencies

None

## Example Playbook

```yaml
- hosts: proxmox_hosts
  roles:
    - role: proxmox_host
```

## License

MIT

## Author

NetBox Proxmox Team
