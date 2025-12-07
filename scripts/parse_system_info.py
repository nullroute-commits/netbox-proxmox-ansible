#!/usr/bin/env python3
"""
Parse automation_nation system information and generate deployment configuration.
This script analyzes the collected system data and determines optimal deployment settings
for networking, hardware resources, and software resources.
"""

import json
import sys
import yaml
from typing import Dict, Any

class DeploymentConfigurator:
    """Analyzes automation_nation output and generates deployment configuration."""
    
    def __init__(self, system_info_file: str):
        """Initialize with path to automation_nation JSON output."""
        with open(system_info_file, 'r') as f:
            self.system_info = json.load(f)
        
        self.config = {
            'deployment_source': 'automation_nation',
            'networking': {},
            'hardware_resources': {},
            'software_resources': {},
            'warnings': [],
            'errors': []
        }
    
    def analyze_hardware(self) -> Dict[str, Any]:
        """Analyze hardware resources and determine container allocations."""
        hw_data = self.system_info.get('get_hardware_info', {}).get('data', {})
        
        # Extract CPU information
        try:
            cpu_cores = int(hw_data.get('cpu_cores', 0))
        except (ValueError, TypeError):
            cpu_cores = 0
            self.config['warnings'].append("Could not parse CPU cores information")
        
        cpu_model = hw_data.get('cpu_model', 'Unknown')
        
        # Extract memory information (convert from MB to GB)
        try:
            memory_total_str = hw_data.get('memory_total', '0 MB')
            memory_total_mb = int(memory_total_str.replace(' MB', '').strip())
            memory_total_gb = memory_total_mb // 1024
        except (ValueError, TypeError, AttributeError):
            memory_total_mb = 0
            memory_total_gb = 0
            self.config['errors'].append("Could not parse memory information")
        
        try:
            memory_available_str = hw_data.get('memory_available', '0 MB')
            memory_available_mb = int(memory_available_str.replace(' MB', '').strip())
        except (ValueError, TypeError, AttributeError):
            memory_available_mb = 0
            self.config['warnings'].append("Could not parse available memory information")
        
        # Extract disk information
        disk_info = hw_data.get('disk_info', [])
        root_disk = next((d for d in disk_info if d.get('mountpoint') == '/'), {})
        disk_available_gb = 0
        if root_disk:
            try:
                available = root_disk.get('available', '0G')
                # Handle different formats: "150G", "1.5T", "1500M"
                if 'T' in available:
                    disk_available_gb = int(float(available.replace('T', '').strip()) * 1024)
                elif 'G' in available:
                    disk_available_gb = int(available.replace('G', '').strip())
                elif 'M' in available:
                    disk_available_gb = int(float(available.replace('M', '').strip()) / 1024)
            except (ValueError, TypeError, AttributeError):
                disk_available_gb = 0
                self.config['warnings'].append("Could not parse disk size information")
        
        hardware_config = {
            'cpu': {
                'model': cpu_model,
                'total_cores': cpu_cores,
                'available_cores': max(0, cpu_cores - 2)  # Reserve 2 for host
            },
            'memory': {
                'total_gb': memory_total_gb,
                'total_mb': memory_total_mb,
                'available_mb': memory_available_mb,
                'reserved_for_host_mb': 2048  # Reserve 2GB for Proxmox host
            },
            'storage': {
                'root_available_gb': disk_available_gb,
                'disk_info': disk_info
            }
        }
        
        # Determine container resource allocations based on available resources
        container_allocations = self._calculate_container_resources(hardware_config)
        hardware_config['container_allocations'] = container_allocations
        
        # Add warnings for insufficient resources
        if memory_total_gb < 8:
            self.config['errors'].append(
                f"Insufficient memory: {memory_total_gb}GB available, 8GB minimum required"
            )
        elif memory_total_gb < 16:
            self.config['warnings'].append(
                f"Limited memory: {memory_total_gb}GB available, 16GB recommended for production"
            )
        
        if disk_available_gb < 100:
            self.config['errors'].append(
                f"Insufficient storage: {disk_available_gb}GB available, 100GB minimum required"
            )
        
        if cpu_cores < 2:
            self.config['errors'].append(
                f"Insufficient CPU cores: {cpu_cores} available, 2 minimum required"
            )
        elif cpu_cores < 4:
            self.config['warnings'].append(
                f"Limited CPU cores: {cpu_cores} available, 4 recommended for production"
            )
        
        return hardware_config
    
    def _calculate_container_resources(self, hardware: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal container resource allocations."""
        total_memory_mb = hardware['memory']['total_mb']
        available_memory_mb = total_memory_mb - hardware['memory']['reserved_for_host_mb']
        total_cores = hardware['cpu']['total_cores']
        
        # Default allocations for minimum system (8GB RAM, 2 cores)
        allocations = {
            'netbox': {
                'cpu': 2,
                'memory': 4096,
                'swap': 2048,
                'disk': 32
            },
            'database': {
                'cpu': 2,
                'memory': 2048,
                'swap': 1024,
                'disk': 16
            },
            'cache': {
                'cpu': 1,
                'memory': 1024,
                'swap': 512,
                'disk': 8
            },
            'proxy': {
                'cpu': 1,
                'memory': 512,
                'swap': 256,
                'disk': 8
            }
        }
        
        # Scale up allocations if more resources are available
        if total_memory_mb >= 16384:  # 16GB+
            allocations['netbox']['memory'] = 6144
            allocations['database']['memory'] = 4096
            allocations['cache']['memory'] = 2048
            allocations['proxy']['memory'] = 1024
        
        if total_memory_mb >= 32768:  # 32GB+
            allocations['netbox']['memory'] = 8192
            allocations['database']['memory'] = 8192
            allocations['cache']['memory'] = 4096
            allocations['proxy']['memory'] = 2048
        
        if total_cores >= 4:
            allocations['netbox']['cpu'] = min(4, max(2, total_cores - 2))
            allocations['database']['cpu'] = 2
        
        if total_cores >= 8:
            allocations['netbox']['cpu'] = 4
            allocations['database']['cpu'] = 4
            allocations['cache']['cpu'] = 2
            allocations['proxy']['cpu'] = 2
        
        # Validate that total allocated memory does not exceed available memory
        total_allocated_memory = sum(container['memory'] for container in allocations.values())
        if total_allocated_memory > available_memory_mb:
            error_msg = (
                f"Total allocated container memory ({total_allocated_memory} MB) exceeds available memory "
                f"({available_memory_mb} MB). Container allocations have been adjusted."
            )
            self.config['warnings'].append(error_msg)
            # Scale down proportionally if needed
            scale_factor = available_memory_mb / total_allocated_memory * 0.9  # Use 90% to leave some headroom
            for container_name in allocations:
                allocations[container_name]['memory'] = int(allocations[container_name]['memory'] * scale_factor)
        
        return allocations
    
    def analyze_networking(self) -> Dict[str, Any]:
        """Analyze network interfaces and suggest configuration."""
        network_data = self.system_info.get('get_ip_info', {}).get('data', {})
        
        interfaces = []
        for iface_name, iface_data in network_data.items():
            if isinstance(iface_data, dict) and 'ipv4_address' in iface_data:
                interfaces.append({
                    'name': iface_name,
                    'ipv4': iface_data.get('ipv4_address'),
                    'ipv6': iface_data.get('ipv6_address'),
                    'mac': iface_data.get('mac_address'),
                    'state': iface_data.get('state')
                })
        
        # Suggest network configuration
        network_config = {
            'detected_interfaces': interfaces,
            'primary_interface': interfaces[0]['name'] if len(interfaces) > 0 else 'eth0',
            'suggested_bridges': {
                'vmbr0': {
                    'comment': 'External network (physical bridge)',
                    'ports': interfaces[0]['name'] if len(interfaces) > 0 else 'eth0',
                    'bridge_fd': 0
                },
                'vmbr1': {
                    'comment': 'Backend network (10.100.0.0/24)',
                    'cidr': '10.100.0.0/24',
                    'gateway': '10.100.0.1',
                    'bridge_fd': 0
                },
                'vmbr2': {
                    'comment': 'DMZ network (10.100.1.0/24)',
                    'cidr': '10.100.1.0/24',
                    'gateway': '10.100.1.1',
                    'bridge_fd': 0
                }
            },
            'nat_configuration': {
                'enabled': True,
                'source_networks': ['10.100.0.0/24', '10.100.1.0/24'],
                'output_interface': 'vmbr0'
            }
        }
        
        if not interfaces:
            self.config['warnings'].append(
                "No network interfaces detected - manual network configuration required"
            )
        
        return network_config
    
    def analyze_software(self) -> Dict[str, Any]:
        """Analyze installed software and check prerequisites."""
        os_data = self.system_info.get('get_os_info', {}).get('data', {})
        packages_data = self.system_info.get('get_packages_and_executables', {}).get('data', {})
        virt_data = self.system_info.get('get_virtualization_info', {}).get('data', {})
        
        software_config = {
            'operating_system': {
                'os_name': os_data.get('os_name'),
                'os_version': os_data.get('os_version'),
                'kernel': os_data.get('kernel_version'),
                'architecture': self.system_info.get('detected_architecture')
            },
            'virtualization': {
                'type': virt_data.get('virt_type'),
                'role': virt_data.get('virt_role'),
                'hypervisor': virt_data.get('hypervisor')
            },
            'package_managers': {},
            'prerequisites': {
                'python3': False,
                'bridge_utils': False,
                'iptables': False
            }
        }
        
        # Check package managers
        if 'package_managers' in packages_data:
            for pm, packages in packages_data['package_managers'].items():
                if packages:
                    software_config['package_managers'][pm] = len(packages)
        
        # Check for required packages
        all_packages = packages_data.get('package_managers', {})
        for pm_packages in all_packages.values():
            if isinstance(pm_packages, list):
                package_names = [p.lower() for p in pm_packages]
                if any('python3' in p for p in package_names):
                    software_config['prerequisites']['python3'] = True
                if any('bridge' in p for p in package_names):
                    software_config['prerequisites']['bridge_utils'] = True
                if any('iptables' in p for p in package_names):
                    software_config['prerequisites']['iptables'] = True
        
        # Check virtualization compatibility
        virt_type = virt_data.get('virt_type', '').lower()
        if 'kvm' not in virt_type and 'none' not in virt_type:
            self.config['warnings'].append(
                f"Unexpected virtualization type: {virt_type} - Proxmox/KVM expected"
            )
        
        return software_config
    
    def generate_config(self) -> Dict[str, Any]:
        """Generate complete deployment configuration."""
        print("Analyzing system information from automation_nation...", file=sys.stderr)
        
        # Analyze each scope
        self.config['hardware_resources'] = self.analyze_hardware()
        self.config['networking'] = self.analyze_networking()
        self.config['software_resources'] = self.analyze_software()
        
        # Add metadata
        self.config['collection_metadata'] = self.system_info.get('collection_metadata', {})
        self.config['analysis_complete'] = True
        
        # Determine deployment readiness
        self.config['deployment_ready'] = len(self.config['errors']) == 0
        
        return self.config
    
    def generate_ansible_vars(self) -> Dict[str, Any]:
        """Generate Ansible variables file from configuration."""
        config = self.generate_config()
        
        if not config['deployment_ready']:
            print("ERROR: System does not meet deployment requirements:", file=sys.stderr)
            for error in config['errors']:
                print(f"  - {error}", file=sys.stderr)
            return None
        
        if config['warnings']:
            print("Warnings:", file=sys.stderr)
            for warning in config['warnings']:
                print(f"  - {warning}", file=sys.stderr)
        
        hw = config['hardware_resources']
        net = config['networking']
        sw = config['software_resources']
        
        # Generate Ansible variables
        ansible_vars = {
            'proxmox_storage': 'local-zfs',
            
            'containers': {
                'netbox': {
                    'vmid': 100,
                    'hostname': 'netbox',
                    'cores': hw['container_allocations']['netbox']['cpu'],
                    'memory': hw['container_allocations']['netbox']['memory'],
                    'swap': hw['container_allocations']['netbox']['swap'],
                    'rootfs_size': hw['container_allocations']['netbox']['disk']
                },
                'database': {
                    'vmid': 101,
                    'hostname': 'netbox-db',
                    'cores': hw['container_allocations']['database']['cpu'],
                    'memory': hw['container_allocations']['database']['memory'],
                    'swap': hw['container_allocations']['database']['swap'],
                    'rootfs_size': hw['container_allocations']['database']['disk']
                },
                'cache': {
                    'vmid': 102,
                    'hostname': 'netbox-redis',
                    'cores': hw['container_allocations']['cache']['cpu'],
                    'memory': hw['container_allocations']['cache']['memory'],
                    'swap': hw['container_allocations']['cache']['swap'],
                    'rootfs_size': hw['container_allocations']['cache']['disk']
                },
                'proxy': {
                    'vmid': 103,
                    'hostname': 'netbox-proxy',
                    'cores': hw['container_allocations']['proxy']['cpu'],
                    'memory': hw['container_allocations']['proxy']['memory'],
                    'swap': hw['container_allocations']['proxy']['swap'],
                    'rootfs_size': hw['container_allocations']['proxy']['disk']
                }
            },
            
            'network_interfaces': {
                'primary': net['primary_interface'],
                'detected': [iface['name'] for iface in net['detected_interfaces']]
            },
            
            'system_capabilities': {
                'total_cpu_cores': hw['cpu']['total_cores'],
                'total_memory_gb': hw['memory']['total_gb'],
                'total_storage_gb': hw['storage']['root_available_gb'],
                'architecture': sw['operating_system']['architecture']
            }
        }
        
        return ansible_vars


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: parse_system_info.py <automation_nation_output.json> [output.yml]", file=sys.stderr)
        print("", file=sys.stderr)
        print("This script parses automation_nation system information and generates", file=sys.stderr)
        print("deployment configuration optimized for the detected hardware.", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        configurator = DeploymentConfigurator(input_file)
        
        # Generate configuration
        if output_file:
            # Generate Ansible vars format
            ansible_vars = configurator.generate_ansible_vars()
            
            if ansible_vars is None:
                sys.exit(1)
            
            # Write to YAML file with comments
            with open(output_file, 'w') as f:
                # Write header comments
                f.write("---\n")
                f.write("# Generated from automation_nation system information\n")
                f.write(f"# Timestamp: {config['collection_metadata'].get('timestamp', 'N/A')}\n")
                f.write(f"# Architecture: {sw['operating_system'].get('architecture', 'N/A')}\n")
                f.write("\n")
                yaml.dump(ansible_vars, f, default_flow_style=False, sort_keys=False)
            
            print(f"\n✓ Deployment configuration written to: {output_file}", file=sys.stderr)
            print(f"\n  Container allocations:", file=sys.stderr)
            for name, spec in ansible_vars['containers'].items():
                print(f"    - {name}: {spec['cores']} CPU, {spec['memory']}MB RAM, {spec['rootfs_size']}GB disk", file=sys.stderr)
        else:
            # Just generate and display JSON config
            config = configurator.generate_config()
            print(json.dumps(config, indent=2))
            
            if not config['deployment_ready']:
                sys.exit(1)
    
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
