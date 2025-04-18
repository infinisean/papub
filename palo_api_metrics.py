import requests
import os
import time
import mysql.connector
import argparse
import logging
from xml.etree import ElementTree as ET

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
    dbcreds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dbcreds')
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

def query_firewall_data(store_number):
    # Construct file paths for the API key and credentials
    base_dir = os.path.dirname(os.path.dirname(__file__))  # One directory level up
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
                parse_system_resources(response.text, hostname)
            else:
                logging.debug(f"Received data for {metric}")
        else:
            logging.error(f"Failed to retrieve data for {metric}. Status code: {response.status_code}")

def parse_system_resources(response_text, hostname):
    # Extract the relevant lines from the response
    lines = response_text.splitlines()
    uptime_line = next(line for line in lines if "up" in line)
    load_avg_line = next(line for line in lines if "load average" in line)
    cpu_line = next(line for line in lines if "%Cpu(s)" in line)
    mem_line = next(line for line in lines if "MiB Mem" in line)

    # Parse the uptime
    uptime = uptime_line.split("up")[1].split(",")[0].strip()

    # Parse the load averages
    load_averages = load_avg_line.split("load average:")[1].strip()

    # Parse the CPU idle and calculate usage
    cpu_idle = float(cpu_line.split(",")[3].split()[0])
    cpu_usage = 100 - cpu_idle

    # Parse the memory usage
    mem_parts = mem_line.split(",")
    mem_total = float(mem_parts[0].split()[2])
    mem_used = float(mem_parts[1].split()[0])
    mem_free = mem_total - mem_used

    # Commented out print statements
    # logging.debug(f"Uptime: {uptime}")
    # logging.debug(f"Load Averages: {load_averages}")
    # logging.debug(f"CPU Usage: {cpu_usage:.2f}%")
    # logging.debug(f"Memory Total: {mem_total:.2f} MiB, Used: {mem_used:.2f} MiB, Free: {mem_free:.2f} MiB")

    # Insert data into MySQL database
    db_host, db_user, db_password, db_name = get_db_credentials()
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = connection.cursor()

    insert_query = """
    INSERT INTO system_resources (timestamp, hostname, uptime, load_averages, cpu_usage, mem_total, mem_used, mem_free)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    data = (time.strftime('%Y-%m-%d %H:%M:%S'), hostname, uptime, load_averages, cpu_usage, mem_total, mem_used, mem_free)
    cursor.execute(insert_query, data)
    connection.commit()

    cursor.close()
    connection.close()

    logging.debug(f"Inserted system resources data for {hostname} into the database")

def main():
    parser = argparse.ArgumentParser(description='Gather metrics for a specified firewall.')
    parser.add_argument('store_number', type=int, help='The 4-digit store number of the firewall')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    setup_logging(args.debug)
    query_firewall_data(args.store_number)

if __name__ == "__main__":
    main()