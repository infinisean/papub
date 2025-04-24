import requests
import os
import time
import mysql.connector
import argparse
import logging
from xml.etree import ElementTree as ET
from xml.dom import minidom



def get_pan_connected_devices(panorama):
    # Define the API command to retrieve connected devices
    command = '<show><devices><connected></connected></devices></show>'
 
    # Use the absolute path for the credentials directory
    base_dir = '/home/netmonitor/.cred'
    pankey_path = os.path.join(base_dir, 'pankey')

    # Read the Panorama API key
    logging.debug(f"Checking if Panorama API key file exists at: {pankey_path}")
    if os.path.exists(pankey_path):
        logging.debug("Panorama API key file found")
        panorama_api_key = read_file(pankey_path)
    else:
        raise FileNotFoundError(f"Panorama API key file '{pankey_path}' not found.")

    headers = {'X-PAN-KEY': panorama_api_key}
    url = f"https://{panorama}/api/?type=op&amp;cmd={command}"
    logging.debug(f"Sending request to Panorama: {url}")
    response = requests.get(url, headers=headers, verify=False)

    # Pretty print the raw response data and write to a temporary file for debugging
    tmp_file_path = f"/tmp/palo/{panorama}_devices_response.xml"
    try:
        xml_pretty_str = minidom.parseString(response.text).toprettyxml(indent="  ")
        with open(tmp_file_path, 'w') as tmp_file:
            tmp_file.write(xml_pretty_str)
        logging.debug(f"Pretty XML response data written to {tmp_file_path}")
    except Exception as e:
        logging.error(f"Failed to pretty print XML: {e}")

    devices_data = []
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        devices = xml_response.findall('.//entry')
        for device in devices:
            hostname = device.find('hostname').text if device.find('hostname') is not None else 'N/A'
            model = device.find('model').text if device.find('model') is not None else 'N/A'
            serial = device.find('serial').text if device.find('serial') is not None else 'N/A'
            mgmt_ip = device.find('ip-address').text if device.find('ip-address') is not None else 'N/A'
            
            # Only add devices where not all fields are "N/A"
            if not (hostname == model == serial == mgmt_ip == 'N/A'):
                devices_data.append({
                    'hostname': hostname,
                    'model': model,
                    'serial': serial,
                    'mgmt_ip': mgmt_ip
                })
        
        # Sort devices by hostname
        devices_data = sorted(devices_data, key=lambda x: x['hostname'])
    else:
        logging.error(f"Failed to retrieve connected devices from {panorama}. Status code: {response.status_code}")

    return devices_data