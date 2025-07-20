"""
Utility functions for parsing firewall command outputs
"""
import re
from typing import List, Dict, Any

def extract_ip_addresses(text: str) -> List[str]:
    """Extract IP addresses from text using regex"""
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.findall(ip_pattern, text)

def extract_mac_addresses(text: str) -> List[str]:
    """Extract MAC addresses from text using regex"""
    mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
    return re.findall(mac_pattern, text)

def parse_table_output(output: str, headers: List[str]) -> List[Dict[str, str]]:
    """Parse table-style command output into list of dictionaries"""
    lines = output.strip().split('\n')
    
    # Skip header lines and find data start
    data_lines = []
    header_found = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for header line
        if not header_found:
            if any(header.lower() in line.lower() for header in headers):
                header_found = True
            continue
        
        # Skip separator lines
        if all(c in '-= ' for c in line):
            continue
            
        data_lines.append(line)
    
    return data_lines

def clean_whitespace(text: str) -> str:
    """Clean up excessive whitespace in text"""
    return ' '.join(text.split())

def extract_numbers(text: str) -> List[int]:
    """Extract all numbers from text"""
    return [int(match) for match in re.findall(r'\d+', text)]

def find_key_value_pairs(text: str, separators: List[str] = [':']) -> Dict[str, str]:
    """Extract key-value pairs from text"""
    pairs = {}
    lines = text.strip().split('\n')
    
    for line in lines:
        for sep in separators:
            if sep in line:
                key, value = line.split(sep, 1)
                pairs[key.strip()] = value.strip()
                break
    
    return pairs