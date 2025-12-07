# Scripts Directory

This directory contains utility scripts for NetBox deployment on Proxmox VE 9.1+.

## Available Scripts

### validate-prerequisites.sh

**Purpose:** Validates that the Proxmox host meets all prerequisites for NetBox deployment.

**Usage:**
```bash
# On Proxmox host as root
./scripts/validate-prerequisites.sh
```

**What it checks:**
- Proxmox VE version (9.0+ required, 9.1+ recommended)
- CPU cores and virtualization support
- Available memory (8GB+ required)
- Storage space (100GB+ required)
- Conflicting VMIDs (100-103)
- Network bridge availability
- Internet connectivity
- DNS resolution
- Required system packages
- Time synchronization
- SSH service status

**Exit Codes:**
- `0`: All checks passed, ready for deployment
- `1`: Some warnings present, may be deployable
- `2`: Critical failures, must be resolved before deployment

**Example Output:**
```
════════════════════════════════════════════════════════════
  NetBox on Proxmox VE 9.1+ - Prerequisites Validation
════════════════════════════════════════════════════════════

1. Checking Proxmox VE version...
   pve-manager/9.1.0/cd9eaafd6fb7e8b0
   ✓ Proxmox VE 9.1 (Compatible with 9.0+)

2. Checking CPU cores...
   CPU cores: 4
   ✓ Sufficient CPU cores (4+ recommended)

...

════════════════════════════════════════════════════════════
  Validation Summary
════════════════════════════════════════════════════════════

Passed:  10 checks
Warnings: 2 checks
Failed:  0 checks

✓ System meets prerequisites for NetBox deployment
```

**Documentation:**
- Full prerequisites: [docs/PREREQUISITES.md](../docs/PREREQUISITES.md)
- Deployment guide: [docs/GREENFIELD_DEPLOYMENT.md](../docs/GREENFIELD_DEPLOYMENT.md)

## Future Scripts

Additional scripts may be added for:
- Automated backup and restore
- Health monitoring
- Performance testing
- Container management utilities
- Migration helpers

## Contributing

When adding new scripts:
1. Follow the naming convention: `verb-noun.sh`
2. Include proper documentation (header comments)
3. Add error handling and exit codes
4. Test on Proxmox VE 9.1+
5. Update this README

## License

MIT License - Same as the main project
