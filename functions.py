import requests
import os
import time
import mysql.connector
import argparse
import logging
from xml.etree import ElementTree as ET
from xml.dom import minidom

def setup_logging(debug_mode):
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    try:
        # Force the logging configuration to override any existing settings
        logging.basicConfig(filename='/tmp/newstream.log', level=logging.DEBUG, format=log_format, force=True)
        
        # Add console logging if debug_mode is True
        if debug_mode:
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            formatter = logging.Formatter(log_format)
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
        
        logging.debug("Logging setup complete.")
    except Exception as e:
        print(f"Failed to set up logging: {e}")
    


def read_file(file_path):
    logging.debug(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    logging.debug(f"Successfully read file: {file_path}")
    return content

def get_db_credentials():
    # Use the absolute path for the credentials directory
    dbcreds_path = os.path.join('/home/netmonitor/.cred', 'dbcreds')
    logging.debug(f"Checking if DB credentials file exists at: {dbcreds_path}")
    if os.path.exists(dbcreds_path):
        logging.debug("DB credentials file found")
        db_creds = read_file(dbcreds_path).split(',')
        if len(db_creds) != 4:
            raise ValueError("DB credentials file 'dbcreds' is not formatted correctly.")
        return db_creds
    else:
        raise FileNotFoundError("DB credentials file 'dbcreds' not found.")

def get_api_key(hostname, username, password):
    logging.debug(f"Generating API key for hostname: {hostname}")
    url = f"https://{hostname}/api/?type=keygen"
    payload = {'user': username, 'password': password}
    response = requests.post(url, data=payload, verify=False)
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        if xml_response.attrib['status'] == 'success':
            logging.debug("API key generation successful")
            return xml_response.find('.//key').text
    logging.error("API key generation failed")
    return None

def query_firewall_data(hostname, live_db):
    # Use the absolute path for the credentials directory
    base_dir = '/home/netmonitor/.cred'
    pankey_path = os.path.join(base_dir, 'pankey')
    pacreds_path = os.path.join(base_dir, 'pacreds')

    # Read the Panorama API key
    logging.debug(f"Checking if Panorama API key file exists at: {pankey_path}")
    if os.path.exists(pankey_path):
        logging.debug("Panorama API key file found")
        panorama_api_key = read_file(pankey_path)
    else:
        raise FileNotFoundError(f"Panorama API key file '{pankey_path}' not found.")

    # Read the Palo Alto credentials
    logging.debug(f"Checking if Palo Alto credentials file exists at: {pacreds_path}")
    if os.path.exists(pacreds_path):
        logging.debug("Palo Alto credentials file found")
        palo_creds = read_file(pacreds_path).split(',')
        if len(palo_creds) != 2:
            raise ValueError("Palo Alto credentials file 'pacreds' is not formatted correctly.")
        palo_username, palo_password = palo_creds
    else:
        raise FileNotFoundError("Palo Alto credentials file 'pacreds' not found.")

    # Use the hostname directly
    api_key = get_api_key(hostname, palo_username, palo_password)

    # Define the API endpoints and commands
    commands = {
        'system_resources': "<show><system><resources></resources></system></show>",
        'arp_table': "<show><arp><entry name='all'></entry></arp></show>"  # Updated ARP command
    }

    headers = {'X-PAN-KEY': api_key}

    for metric, cmd in commands.items():
        url = f"https://{hostname}/api/?type=op&cmd={cmd}"
        logging.debug(f"Sending request to URL: {url}")
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            if metric == 'system_resources':
                parse_system_resources(response.text, hostname, live_db)
            else:
                logging.debug(f"Received data for {metric}")
        else:
            logging.error(f"Failed to retrieve data for {metric}. Status code: {response.status_code}")

def parse_system_resources(response_text, hostname, live_db):
    # Extract the relevant lines from the response
    lines = response_text.splitlines()
    try:
        uptime_line = next(line for line in lines if "up" in line)
        load_avg_line = next(line for line in lines if "load average" in line)
        cpu_line = next(line for line in lines if "%Cpu(s)" in line)
        mem_line = next(line for line in lines if "MiB Mem" in line)
    except StopIteration as e:
        logging.error("Failed to parse system resources: required line not found")
        return

    # Parse the uptime
    uptime = uptime_line.split("up")[1].split(",")[0].strip()

    # Parse the load averages
    load_averages = load_avg_line.split("load average:")[1].strip()
    one_min_load = float(load_averages.split(",")[0].strip())

    # Parse the CPU idle and calculate usage
    try:
        cpu_idle = float(cpu_line.split(",")[3].split()[0])
        cpu_usage = 100 - cpu_idle
    except (ValueError, IndexError) as e:
        logging.error(f"Failed to parse CPU usage: {e}")
        return

    # Parse the memory usage
    try:
        mem_parts = mem_line.split(",")
        mem_used = float(mem_parts[1].split()[0])
        mem_free = float(mem_parts[2].split()[0])
    except (ValueError, IndexError) as e:
        logging.error(f"Failed to parse memory usage: {e}")
        return

    # Prepare data for insertion
    data = (hostname, uptime, one_min_load, cpu_usage, mem_used, mem_free)
    insert_query = """
    INSERT INTO system_resources (hostname, updated, bu, retail_store_id, last_boot, one_min_load, cpu_usage, mem_used, mem_free)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    if live_db:
        # Insert data into MySQL database
        db_host, db_user, db_password, db_name = get_db_credentials()
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = connection.cursor()
        cursor.execute(insert_query, data)
        connection.commit()
        cursor.close()
        connection.close()
        logging.debug(f"Inserted system resources data for {hostname} into the database")
    else:
        # Print the SQL query for debugging
        logging.debug(f"SQL Query: {insert_query % data}")

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
    url = f"https://{panorama}/api/?type=op&cmd={command}"
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

def get_primary_pan(panorama_instances):
    for panorama in panorama_instances:
        logging.debug(f"Checking Panorama instance: {panorama}")
        # Define the API command to retrieve HA state
        command = "<show><high-availability><state></state></high-availability></show>"
        
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
        url = f"https://{panorama}/api/?type=op&cmd={command}"
        logging.debug(f"Sending request to Panorama: {url}")
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            xml_response = ET.fromstring(response.text)
            ha_state = xml_response.find('.//result/state')
            if ha_state is not None:
                state_text = ha_state.text.strip().lower()
                logging.debug(f"HA state for {panorama}: {state_text}")
                if 'active' in state_text:  # Check for the presence of "active"
                    logging.debug(f"Primary Panorama instance found: {panorama}")
                    return panorama
        else:
            logging.error(f"Failed to retrieve HA state from {panorama}. Status code: {response.status_code}")

    logging.error("No active Panorama instance found.")
    return None

