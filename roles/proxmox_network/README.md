# Proxmox Network Role

Create and configure network bridges for Proxmox VE.

## Requirements

- Proxmox VE 8.x or 9.x
- `proxmox_host` role applied
- Root or sudo access

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `proxmox_network_backend` | See defaults | Backend network config |
| `proxmox_network_dmz` | See defaults | DMZ network config |
| `proxmox_network_external` | See defaults | External network config |
| `proxmox_network_nat_enabled` | `true` | Enable NAT |
| `proxmox_network_nat_networks` | See defaults | Networks to NAT |
| `proxmox_network_nat_output_interface` | `vmbr0` | NAT output interface |
| `proxmox_network_iptables_rules` | `/etc/iptables/rules.v4` | IPtables rules file |

## Handlers

| Handler | Description |
|---------|-------------|
| `iptables_reload` | Reload iptables rules |

## Dependencies

- `proxmox_host`

## Example Playbook

```yaml
- hosts: proxmox_hosts
  roles:
    - role: proxmox_network
      vars:
        backend_network:
          name: vmbr1
          cidr: 10.100.0.0/24
          gateway: 10.100.0.1
```

## License

MIT

## Author

NetBox Proxmox Team
