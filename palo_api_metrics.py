import requests
import os
import time
import mysql.connector
import argparse
import logging
from xml.etree import ElementTree as ET

def get_pan_connected_devices(panorama):
    # Define the API command to retrieve connected devices
    command = "&lt;show&gt;&lt;devices&gt;&lt;connected&gt;&lt;/connected&gt;&lt;/devices&gt;&lt;/show&gt;"

    # Update the base directory to include the ../.cred directory
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../.cred')
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

    devices_data = []
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        devices = xml_response.findall('.//entry')
        for device in devices:
            hostname = device.find('hostname').text if device.find('hostname') is not None else 'N/A'
            model = device.find('model').text if device.find('model') is not None else 'N/A'
            serial = device.find('serial').text if device.find('serial') is not None else 'N/A'
            mgmt_ip = device.find('ip-address').text if device.find('ip-address') is not None else 'N/A'
            devices_data.append({
                'hostname': hostname,
                'model': model,
                'serial': serial,
                'mgmt_ip': mgmt_ip
            })
    else:
        logging.error(f"Failed to retrieve connected devices from {panorama}. Status code: {response.status_code}")

    return devices_data

def setup_logging(debug_mode):
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename='metrics.log', level=logging.DEBUG, format=log_format)
    if debug_mode:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter(log_format)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

def read_file(file_path):
    logging.debug(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    logging.debug(f"Successfully read file: {file_path}")
    return content

def get_db_credentials():
    # Update the path to look in the ../.cred directory
    dbcreds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../.cred', 'dbcreds')
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

def query_firewall_data(store_number, live_db):
    # Update the base directory to include the ../.cred directory
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../.cred')
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

    hostname = f"S{int(store_number):04d}MLANF01"
    api_key = get_api_key(hostname, palo_username, palo_password)

    # Define the API endpoints and commands
    commands = {
        'system_resources': "&lt;show&gt;&lt;system&gt;&lt;resources&gt;&lt;/resources&gt;&lt;/system&gt;&lt;/show&gt;",
        'arp_table': "&lt;show&gt;&lt;arp&gt;&lt;entry name='all'&gt;&lt;/entry&gt;&lt;/arp&gt;&lt;/show&gt;"  # Updated ARP command
    }

    headers = {'X-PAN-KEY': api_key}

    for metric, cmd in commands.items():
        url = f"https://{hostname}/api/?type=op&amp;cmd={cmd}"
        logging.debug(f"Sending request to URL: {url}")
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            if metric == 'system_resources':
                parse_system_resources(response.text, hostname, store_number, live_db)
            else:
                logging.debug(f"Received data for {metric}")
        else:
            logging.error(f"Failed to retrieve data for {metric}. Status code: {response.status_code}")

def parse_system_resources(response_text, hostname, store_number, live_db):
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
    data = (hostname, uptime, one_min_load, cpu_usage, mem_used, mem_free, store_number)
    insert_query = """
    INSERT INTO system_resources (hostname, last_boot, one_min_load, cpu_usage, mem_used, mem_free, retail_store)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
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

def main():
    parser = argparse.ArgumentParser(description='Gather metrics for a specified firewall.')
    parser.add_argument('store_number', type=int, help='The 4-digit store number of the firewall')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--live-db', action='store_true', help='Insert data into the live database')
    parser.add_argument('--invocation', choices=['cli', 'streamlit'], default='cli', help='Specify the invocation method')
    args = parser.parse_args()

    setup_logging(args.debug)
    logging.debug(f"Invocation method: {args.invocation}")

    # Example usage of get_pan_connected_devices
    panorama_instances = ['a46panorama', 'l17panorama']  # Replace with actual Panorama hostnames
    for panorama in panorama_instances:
        devices = get_pan_connected_devices(panorama)
        for device in devices:
            print(f"Hostname: {device['hostname']}, Model: {device['model']}, Serial: {device['serial']}, Mgmt IP: {device['mgmt_ip']}")
        print(f"Total connected devices from {panorama}: {len(devices)}")

    # query_firewall_data(args.store_number, args.live_db)

if __name__ == "__main__":
    main()