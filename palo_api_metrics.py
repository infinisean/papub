import requests
import csv
import os
import time
from xml.etree import ElementTree as ET

def query_firewall_data(hostname, api_key):
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
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            # Save the raw response to a file
            raw_file = f"/tmp/{hostname}-{metric}-{time.strftime('%Y%m%d-%H%M%S')}.txt"
            with open(raw_file, 'w') as file:
                file.write(response.text)
                print(f"Saved raw output for {metric} to {raw_file}")
        else:
            print(f"Failed to retrieve data for {metric}. Status code: {response.status_code}")

def get_api_key(hostname, username, password):
    url = f"https://{hostname}/api/?type=keygen"
    payload = {'user': username, 'password': password}
    response = requests.post(url, data=payload, verify=False)
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        if xml_response.attrib['status'] == 'success':
            return xml_response.find('.//key').text
    return None