# Debian Base Role

Configure baseline Debian container settings for LXC containers on Proxmox VE.

## Requirements

- Proxmox VE 8.x or 9.x
- LXC container created with `proxmox_container` role
- Network connectivity to public repositories

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `debian_base_packages` | See defaults | List of packages to install |
| `debian_base_locale` | `en_US.UTF-8` | Locale to generate |
| `debian_base_timezone` | `UTC` | Timezone to set |
| `debian_base_nameservers` | `["8.8.8.8", "8.8.4.4"]` | DNS nameservers |
| `debian_base_test_connectivity` | `true` | Test internet connectivity |

## Dependencies

None

## Example Playbook

```yaml
- hosts: proxmox_hosts
  roles:
    - role: debian_base
      vars:
        container:
          vmid: 100
```

## License

MIT

## Author

NetBox Proxmox Team
