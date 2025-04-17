import requests
import csv
import os
import time
from xml.etree import ElementTree as ET

def read_file(file_path):
    print(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    print(f"Successfully read file: {file_path}")
    return content

def get_api_key(hostname, username, password):
    print(f"Generating API key for hostname: {hostname}")
    url = f"https://{hostname}/api/?type=keygen"
    payload = {'user': username, 'password': password}
    response = requests.post(url, data=payload, verify=False)
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        if xml_response.attrib['status'] == 'success':
            print("API key generation successful")
            return xml_response.find('.//key').text
    print("API key generation failed")
    return None

def query_firewall_data(store_number):
    # Construct file paths for the API key and credentials
    base_dir = os.path.dirname(os.path.dirname(__file__))  # One directory level up
    pankey_path = os.path.join(base_dir, 'pankey')
    pacreds_path = os.path.join(base_dir, 'pacreds')

    # Read the Panorama API key
    print(f"Checking if Panorama API key file exists at: {pankey_path}")
    if os.path.exists(pankey_path):
        print("Panorama API key file found")
        panorama_api_key = read_file(pankey_path)
    else:
        raise FileNotFoundError("Panorama API key file 'pankey' not found.")

    # Read the Palo Alto credentials
    print(f"Checking if Palo Alto credentials file exists at: {pacreds_path}")
    if os.path.exists(pacreds_path):
        print("Palo Alto credentials file found")
        palo_creds = read_file(pacreds_path).split(',')
        if len(palo_creds) != 2:
            raise ValueError("Palo Alto credentials file 'pacreds' is not formatted correctly.")
        palo_username, palo_password = palo_creds
    else:
        raise FileNotFoundError("Palo Alto credentials file 'pacreds' not found.")

    hostname = f"S{int(store_number):04d}MLANF01"
    api_key = get_api_key(hostname, palo_username, palo_password)

    # Define the API endpoints and commands
    commands = {
        'cpu_usage': "<show><system><resources></resources></system></show>",
        'ram_usage': "<show><system><resources></resources></system></show>",
        'concurrent_connections': "<show><session><info></info></session></show>",
        'arp_table': "<show><arp><all></all></arp></show>"
    }

    headers = {'X-PAN-KEY': api_key}

    # Ensure the /tmp directory exists
    if not os.path.exists("/tmp"):
        os.makedirs("/tmp")

    for metric, cmd in commands.items():
        url = f"https://{hostname}/api/?type=op&cmd={cmd}"
        print(f"Sending request to URL: {url}")
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            # Save the raw txt response to a file (not all output will be in XML... do not change the extension)
            raw_file = f"/tmp/{hostname}-{metric}-{time.strftime('%Y%m%d-%H%M%S')}.txt"
            with open(raw_file, 'w') as file:
                file.write(response.text)
            print(f"Saved raw output for {metric} to {raw_file}")
        else:
            print(f"Failed to retrieve data for {metric}. Status code: {response.status_code}")