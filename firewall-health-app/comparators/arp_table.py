"""
ARP table comparator for firewall health metrics
"""
import re
from typing import Dict, Any, Set, List
from .base import BaseComparator, ComparisonResult, ComparisonStatus
from .utils import extract_ip_addresses, parse_table_output, clean_whitespace

class ArpTableComparator(BaseComparator):
    """Comparator for 'show arp all' command output"""
    
    def __init__(self):
        super().__init__("show_arp_all")
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse ARP table output into structured data"""
        arp_entries = []
        ip_addresses = set()
        mac_addresses = set()
        interfaces = set()
        
        lines = output.strip().split('\n')
        
        # Look for ARP table entries - typical format:
        # Interface     IP address      HW address           Status
        for line in lines:
            line = clean_whitespace(line)
            
            # Skip header and separator lines
            if any(header in line.lower() for header in ['interface', 'ip address', 'hw address', 'status']):
                continue
            if all(c in '-= ' for c in line):
                continue
            if not line:
                continue
                
            # Parse line - look for IP and MAC patterns
            ip_matches = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)
            mac_matches = re.findall(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
            
            if ip_matches and mac_matches:
                parts = line.split()
                if len(parts) >= 3:
                    interface = parts[0] if parts[0] != ip_matches[0] else "unknown"
                    ip_addr = ip_matches[0]
                    mac_addr = mac_matches[0]
                    status = "active"  # Default status
                    
                    # Look for status information
                    if len(parts) > 3:
                        status = parts[-1].lower()
                    
                    arp_entry = {
                        'interface': interface,
                        'ip': ip_addr,
                        'mac': mac_addr,
                        'status': status
                    }
                    
                    arp_entries.append(arp_entry)
                    ip_addresses.add(ip_addr)
                    mac_addresses.add(mac_addr)
                    interfaces.add(interface)
        
        return {
            'entries': arp_entries,
            'ip_addresses': ip_addresses,
            'mac_addresses': mac_addresses,
            'interfaces': interfaces,
            'total_entries': len(arp_entries),
            'active_entries': len([e for e in arp_entries if e['status'] == 'active'])
        }
    
    def compare(self, pre_data: Dict[str, Any], post_data: Dict[str, Any]) -> ComparisonResult:
        """Compare ARP table data"""
        pre_ips = pre_data.get('ip_addresses', set())
        post_ips = post_data.get('ip_addresses', set())
        pre_macs = pre_data.get('mac_addresses', set())
        post_macs = post_data.get('mac_addresses', set())
        
        pre_count = pre_data.get('total_entries', 0)
        post_count = post_data.get('total_entries', 0)
        
        # Calculate changes
        missing_ips = pre_ips - post_ips
        new_ips = post_ips - pre_ips
        missing_macs = pre_macs - post_macs
        new_macs = post_macs - pre_macs
        
        count_change = post_count - pre_count
        
        # Determine status and message
        if not missing_ips and not missing_macs and abs(count_change) <= 1:
            status = ComparisonStatus.SUCCESS
            message = f"ARP table unchanged ✅ ({post_count} entries)"
        elif missing_ips or missing_macs or count_change < -2:
            status = ComparisonStatus.ERROR
            message_parts = []
            
            if count_change < 0:
                message_parts.append(f"{abs(count_change)} fewer ARP entries")
            
            if missing_ips:
                ip_list = ", ".join(sorted(list(missing_ips))[:5])  # Show first 5
                if len(missing_ips) > 5:
                    ip_list += f" (and {len(missing_ips) - 5} more)"
                message_parts.append(f"IPs {ip_list} no longer responding")
            
            message = " - ".join(message_parts) + " ❌"
        else:
            status = ComparisonStatus.WARNING
            message_parts = []
            
            if count_change > 0:
                message_parts.append(f"{count_change} new ARP entries")
            
            if new_ips:
                ip_list = ", ".join(sorted(list(new_ips))[:3])
                if len(new_ips) > 3:
                    ip_list += f" (and {len(new_ips) - 3} more)"
                message_parts.append(f"new IPs: {ip_list}")
            
            message = " - ".join(message_parts) + " ⚠️"
        
        # Prepare detailed metrics
        metrics = {
            'pre_count': pre_count,
            'post_count': post_count,
            'count_change': count_change,
            'missing_ips_count': len(missing_ips),
            'new_ips_count': len(new_ips),
            'missing_macs_count': len(missing_macs),
            'new_macs_count': len(new_macs)
        }
        
        details = {
            'missing_ips': list(missing_ips),
            'new_ips': list(new_ips),
            'missing_macs': list(missing_macs),
            'new_macs': list(new_macs)
        }
        
        return ComparisonResult(
            status=status,
            message=message,
            details=details,
            metrics=metrics
        )