#!/bin/bash
# NetBox Deployment Prerequisites Validation Script
# Run on Proxmox VE 9.1+ host as root
# Purpose: Validate system meets requirements before deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "  NetBox on Proxmox VE 9.1+ - Prerequisites Validation"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "This script validates your Proxmox host meets the requirements"
echo "for deploying NetBox using the Ansible automation framework."
echo ""
echo "System information collection: automation_nation.git"
echo "  https://github.com/nullroute-commits/automation_nation.git"
echo "  Use ./collect_info.sh to gather detailed system capabilities"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Initialize counters
pass_count=0
warn_count=0
fail_count=0

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ Error: This script must be run as root${NC}"
    exit 1
fi

# Function to print status
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        pass)
            echo -e "${GREEN}✓${NC} $message"
            ((pass_count++))
            ;;
        warn)
            echo -e "${YELLOW}⚠${NC} $message"
            ((warn_count++))
            ;;
        fail)
            echo -e "${RED}✗${NC} $message"
            ((fail_count++))
            ;;
        *)
            echo "  $message"
            ;;
    esac
}

# 1. Check Proxmox version
echo "1. Checking Proxmox VE version..."
if command -v pveversion &> /dev/null; then
    pve_output=$(pveversion | head -1)
    echo "   $pve_output"
    pve_version=$(echo "$pve_output" | grep -oP 'pve-manager/\K[0-9.]+' | cut -d. -f1,2)
    
    if [ -n "$pve_version" ]; then
        # Convert version to comparable number
        pve_major=$(echo "$pve_version" | cut -d. -f1)
        pve_minor=$(echo "$pve_version" | cut -d. -f2)
        
        if [ "$pve_major" -gt 9 ] || ([ "$pve_major" -eq 9 ] && [ "$pve_minor" -ge 0 ]); then
            print_status "pass" "Proxmox VE $pve_version (Compatible with 9.0+)"
        else
            print_status "fail" "Proxmox VE $pve_version (Requires 9.0 or later)"
        fi
    else
        print_status "fail" "Could not determine Proxmox version"
    fi
else
    print_status "fail" "Proxmox VE not detected (pveversion not found)"
fi
echo ""

# 2. Check CPU cores
echo "2. Checking CPU cores..."
cpu_cores=$(grep -c ^processor /proc/cpuinfo)
echo "   CPU cores: $cpu_cores"
if [ $cpu_cores -ge 4 ]; then
    print_status "pass" "Sufficient CPU cores (4+ recommended)"
elif [ $cpu_cores -ge 2 ]; then
    print_status "warn" "Minimum CPU cores met (2), but 4+ recommended for production"
else
    print_status "fail" "Insufficient CPU cores (minimum 2 required)"
fi
echo ""

# 3. Check virtualization support
echo "3. Checking CPU virtualization support..."
virt_support=$(egrep -c '(vmx|svm)' /proc/cpuinfo)
if [ $virt_support -gt 0 ]; then
    virt_type=$(egrep -o '(vmx|svm)' /proc/cpuinfo | head -1)
    if [ "$virt_type" = "vmx" ]; then
        print_status "pass" "Intel VT-x virtualization enabled"
    else
        print_status "pass" "AMD-V virtualization enabled"
    fi
else
    print_status "fail" "CPU virtualization support not detected (VT-x/AMD-V required)"
fi
echo ""

# 4. Check available memory
echo "4. Checking available memory..."
mem_total=$(free -g | awk '/^Mem:/ {print $2}')
mem_available=$(free -g | awk '/^Mem:/ {print $7}')
echo "   Total memory: ${mem_total}GB"
echo "   Available memory: ${mem_available}GB"
if [ $mem_available -ge 16 ]; then
    print_status "pass" "Excellent memory available (16GB+)"
elif [ $mem_available -ge 8 ]; then
    print_status "pass" "Sufficient memory available (8GB+)"
else
    print_status "warn" "Low available memory (less than 8GB) - deployment may fail"
fi
echo ""

# 5. Check storage space
echo "5. Checking storage space..."
if [ -d /var/lib/vz ]; then
    storage_total=$(df -BG /var/lib/vz | awk 'NR==2 {print $2}' | sed 's/G//')
    storage_available=$(df -BG /var/lib/vz | awk 'NR==2 {print $4}' | sed 's/G//')
    echo "   Storage path: /var/lib/vz"
    echo "   Total storage: ${storage_total}GB"
    echo "   Available storage: ${storage_available}GB"
    
    if [ $storage_available -ge 200 ]; then
        print_status "pass" "Excellent storage available (200GB+)"
    elif [ $storage_available -ge 100 ]; then
        print_status "pass" "Sufficient storage available (100GB+)"
    else
        print_status "warn" "Low storage space (less than 100GB) - may be insufficient"
    fi
else
    print_status "fail" "Storage directory /var/lib/vz not found"
fi
echo ""

# 6. Check for conflicting VMIDs
echo "6. Checking for conflicting container VMIDs..."
if command -v pct &> /dev/null; then
    conflict_vms=$(pct list | grep -E "^(100|101|102|103)" | wc -l)
    if [ $conflict_vms -eq 0 ]; then
        print_status "pass" "No conflicting VMIDs (100-103 are available)"
    else
        print_status "fail" "Found $conflict_vms conflicting VMIDs:"
        pct list | grep -E "^(100|101|102|103)" | sed 's/^/   /'
    fi
else
    print_status "warn" "Cannot check VMIDs (pct command not found)"
fi
echo ""

# 7. Check for conflicting bridges
echo "7. Checking for conflicting network bridges..."
if command -v brctl &> /dev/null; then
    if brctl show 2>/dev/null | grep -qE "^(vmbr1|vmbr2)"; then
        print_status "warn" "Bridges vmbr1 or vmbr2 already exist (will be reconfigured):"
        brctl show | grep -E "^(vmbr1|vmbr2)" | sed 's/^/   /'
    else
        print_status "pass" "No conflicting bridges (vmbr1, vmbr2 will be created)"
    fi
    
    # Check vmbr0 exists
    if brctl show 2>/dev/null | grep -q "^vmbr0"; then
        print_status "pass" "External bridge vmbr0 exists"
    else
        print_status "warn" "External bridge vmbr0 not found (may need manual configuration)"
    fi
else
    print_status "warn" "Cannot check bridges (bridge-utils not installed yet)"
fi
echo ""

# 8. Check internet connectivity
echo "8. Checking internet connectivity..."
if ping -c 2 -W 5 debian.org > /dev/null 2>&1; then
    print_status "pass" "Internet connectivity available (debian.org reachable)"
else
    print_status "fail" "No internet connectivity (cannot reach debian.org)"
fi
echo ""

# 9. Check DNS resolution
echo "9. Checking DNS resolution..."
if nslookup github.com > /dev/null 2>&1; then
    print_status "pass" "DNS resolution working (github.com resolved)"
elif host github.com > /dev/null 2>&1; then
    print_status "pass" "DNS resolution working (github.com resolved)"
else
    print_status "fail" "DNS resolution failed (cannot resolve github.com)"
fi
echo ""

# 10. Check required packages
echo "10. Checking system packages..."
required_packages=("bridge-utils" "python3")
optional_packages=("python3-proxmoxer" "iptables-persistent")

for pkg in "${required_packages[@]}"; do
    if dpkg -l 2>/dev/null | grep -q "^ii  $pkg "; then
        print_status "pass" "$pkg is installed"
    else
        print_status "warn" "$pkg not installed (will be installed during deployment)"
    fi
done

for pkg in "${optional_packages[@]}"; do
    if dpkg -l 2>/dev/null | grep -q "^ii  $pkg "; then
        echo "   ✓ $pkg is installed"
    else
        echo "   - $pkg not installed (will be installed during deployment)"
    fi
done
echo ""

# 11. Check time synchronization
echo "11. Checking time synchronization..."
if systemctl is-active --quiet chronyd || systemctl is-active --quiet systemd-timesyncd; then
    print_status "pass" "Time synchronization service is active"
else
    print_status "warn" "Time synchronization service not active (recommended for containers)"
fi
echo ""

# 12. Check SSH service
echo "12. Checking SSH service..."
if systemctl is-active --quiet sshd || systemctl is-active --quiet ssh; then
    print_status "pass" "SSH service is active"
else
    print_status "fail" "SSH service is not active (required for Ansible)"
fi
echo ""

# Print summary
echo "════════════════════════════════════════════════════════════"
echo "  Validation Summary"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Passed:${NC}  $pass_count checks"
echo -e "${YELLOW}Warnings:${NC} $warn_count checks"
echo -e "${RED}Failed:${NC}  $fail_count checks"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ System meets prerequisites for NetBox deployment${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review any warnings above and address if needed"
    echo "  2. Use automation_nation.git to collect detailed system info"
    echo "  3. Review docs/GREENFIELD_DEPLOYMENT.md for deployment guide"
    echo "  4. Run: ansible-playbook playbooks/greenfield-deployment.yml"
    exit_code=0
elif [ $fail_count -le 2 ] && [ $warn_count -gt 0 ]; then
    echo -e "${YELLOW}⚠ System has some issues but may be deployable${NC}"
    echo ""
    echo "Action required:"
    echo "  1. Review and resolve failed checks above"
    echo "  2. Address critical warnings"
    echo "  3. Consult docs/PREREQUISITES.md for detailed requirements"
    exit_code=1
else
    echo -e "${RED}✗ System does not meet prerequisites for deployment${NC}"
    echo ""
    echo "Action required:"
    echo "  1. Resolve all failed checks above"
    echo "  2. Review docs/PREREQUISITES.md for detailed requirements"
    echo "  3. Use automation_nation.git to collect system information"
    echo "  4. Re-run this validation script after fixes"
    exit_code=2
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Documentation:"
echo "  Prerequisites: docs/PREREQUISITES.md"
echo "  System Info Tool: https://github.com/nullroute-commits/automation_nation.git"
echo "  Deployment Guide: docs/GREENFIELD_DEPLOYMENT.md"
echo "  Architecture: docs/ARCHITECTURE.md"
echo ""

exit $exit_code
