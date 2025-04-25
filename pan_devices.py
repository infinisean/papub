import requests
import os
import json
from xml.etree import ElementTree as ET
import logging
import functions

def read_file(file_path):
    logging.debug(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    logging.debug(f"Successfully read file: {file_path}")
    return content

def get_pan_devices(active_panorama):
    
    # Define the API command to retrieve connected devices
    command = '<show><devices><connected></connected></devices></show>'

    pankey = read_pan_api_key()

    # Read the Panorama API key
    if os.path.exists(pankey_path):
        panorama_api_key = read_file(pankey_path)
    else:
        raise FileNotFoundError(f"Panorama API key file '{pankey_path}' not found.")

    headers = {'X-PAN-KEY': panorama_api_key}
    url = f"https://{active_panorama}/api/?type=op&cmd={command}"
    logging.debug(f"Sending request to Panorama: {url}")
    response = requests.get(url, headers=headers, verify=False)

    devices_data = []
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        
        # Debug: Write the raw XML response to a file
        raw_xml_path = "/tmp/palo/raw_devices.xml"
        with open(raw_xml_path, 'w') as file:
            file.write(response.text)
        logging.debug(f"Raw XML response written to {raw_xml_path}")

        devices = xml_response.findall('.//entry')
        for device in devices:
            # Debug: Print the device XML for inspection
            logging.debug(f"Device XML: {ET.tostring(device, encoding='unicode')}")

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
    else:
        logging.error(f"Failed to retrieve connected devices from {active_panorama}. Status code: {response.status_code}")

    # Write the devices data to a JSON file
    json_file_path = "/tmp/palo/connected_devices.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(devices_data, json_file, indent=4)
    logging.debug(f"Connected devices data written to {json_file_path}")

# Example usage
if __name__ == "__main__":
    active_panorama = "A46PANORAMA"  # Replace with the actual active Panorama instance
    get_pan_devices(active_panorama)