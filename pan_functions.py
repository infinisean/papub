import requests
import os
import time
import mysql.connector
import argparse
import logging
from xml.etree import ElementTree as ET
from xml.dom import minidom
import pandas as pd


def setup_logging(debug_mode):
    # Define a log format that includes the script name and line number
    log_format = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
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

def palo_gen_api_key(hostname, username, password):
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

def read_pan_api_key():
    """
    Function to read the Panorama API key from a file.
    
    :return: The API key as a string.
    :raises FileNotFoundError: If the API key file is not found.
    """
    base_dir = '/home/netmonitor/.cred'
    pankey_path = os.path.join(base_dir, 'pankey')

    logging.debug(f"Checking if Panorama API key file exists at: {pankey_path}")
    if os.path.exists(pankey_path):
        logging.debug("Panorama API key file found")
        return read_file(pankey_path)
    else:
        raise FileNotFoundError(f"Panorama API key file '{pankey_path}' not found.")

def send_api_query(hostname, api_key, query_type, command):
    """
    Centralized function to handle API queries.
    
    :param hostname: The hostname of the Panorama instance.
    :param command: The API command to execute.
    :param api_key: The API key for authentication.
    :param query_type: The type of query (e.g., "op", "config").
    :return: The raw response text from the API query.
    """
    headers = {'X-PAN-KEY': api_key}
    url = f"https://{hostname}/api/?type={query_type}&cmd={command}"
    
    with requests.Session() as session:
        session.headers.update(headers)
        logging.debug(f"Sending request to {hostname}: {url}")
        response = session.get(url, verify=False)
        
        if response.status_code == 200:
            logging.debug(f"Received response from {hostname}")
            return response.text
        else:
            logging.error(f"Failed to retrieve data from {hostname}. Status code: {response.status_code}")
            return None

def get_pan_connected_devices(active_panorama):
    # Define the API command to retrieve connected devices
    query_type = 'op'
    command = '<show><devices><connected></connected></devices></show>'
    
    
    # Read the Panorama API key
    pan_api_key = read_pan_api_key()

    # Use the centralized API query function
    raw_response = send_api_query(active_panorama, pan_api_key, query_type, command)
    if raw_response is None:
        return []

    # Parse the response
    devices_data = []
    try:
        xml_response = ET.fromstring(raw_response)
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
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML response: {e}")

    return devices_data

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

def get_active_pan(panorama_instances):
    # Open a file for writing debug information
    with open('/tmp/get_active_pan_debug.log', 'w') as debug_file:
        for panorama in panorama_instances:
            debug_file.write(f"Checking Panorama instance: {panorama}\n")
            # Define the API command to retrieve HA state
            command = "<show><high-availability><state></state></high-availability></show>"
            
            # Use the absolute path for the credentials directory
            base_dir = '/home/netmonitor/.cred'
            pankey_path = os.path.join(base_dir, 'pankey')

            # Read the Panorama API key
            debug_file.write(f"Checking if Panorama API key file exists at: {pankey_path}\n")
            if os.path.exists(pankey_path):
                debug_file.write("Panorama API key file found\n")
                pan_api_key = read_file(pankey_path)
            else:
                debug_file.write(f"Panorama API key file '{pankey_path}' not found.\n")
                continue

            headers = {'X-PAN-KEY': pan_api_key}
            url = f"https://{panorama}/api/?type=op&cmd={command}"
            debug_file.write(f"Sending request to Panorama: {url}\n")
            try:
                response = requests.get(url, headers=headers, verify=False)
                debug_file.write(f"Response status code: {response.status_code}\n")
                debug_file.write(f"Response text: {response.text}\n")  # Log the first 500 characters of the response
            except Exception as e:
                debug_file.write(f"Exception occurred while sending request: {e}\n")
                continue

            if response.status_code == 200:
                try:
                    xml_response = ET.fromstring(response.text)
                    # Look for the <state> element under <local-info>
                    ha_state = xml_response.find('.//local-info/state')
                    if ha_state is not None:
                        state_text = ha_state.text.strip().lower()
                        debug_file.write(f"HA state for {panorama}: {state_text}\n")
                        # Check for specific active states
                        if state_text in ['primary-active', 'secondary-active']:
                            debug_file.write(f"Primary Panorama instance found: {panorama}\n")
                            return panorama
                except ET.ParseError as e:
                    debug_file.write(f"Failed to parse XML response: {e}\n")
            else:
                debug_file.write(f"Failed to retrieve HA state from {panorama}. Status code: {response.status_code}\n")

        debug_file.write("No active Panorama instance found.\n")
    return None

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
    return devices_data

def parse_element_to_dict(element, parent_tag=""):
    """Recursively parse XML elements and return a dictionary."""
    data = {}
    for child in element:
        tag = f"{parent_tag}/{child.tag}" if parent_tag else child.tag
        if len(child):  # If the element has children, recurse
            data.update(parse_element_to_dict(child, tag))
        else:
            data[tag] = child.text
    return data

def get_pan_ha_state(panorama_instances):
    ha_states = {}
    for panorama in panorama_instances:
        command = "<show><high-availability><state></state></high-availability></show>" #DO NOT CHANGE THIS LINE AT ALL

        base_dir = '/home/netmonitor/.cred'
        pankey_path = os.path.join(base_dir, 'pankey')

        # Read the Panorama API key
        if os.path.exists(pankey_path):
            panorama_api_key = read_file(pankey_path)
        else:
            st.error(f"Panorama API key file '{pankey_path}' not found.")
            return

        headers = {'X-PAN-KEY': panorama_api_key}
        url = f"https://{panorama}/api/?type=op&cmd={command}" #DO NOT CHANGE THIS LINE AT ALL
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            # Save raw XML response to a file
            raw_data_path = f"/tmp/palo/{panorama}_ha-state.txt"
            os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)
            with open(raw_data_path, 'w') as file:
                file.write(response.text)

            xml_response = ET.fromstring(response.text)
            ha_state = xml_response.find('.//result')
            if ha_state is not None:
                ha_states[panorama] = parse_element_to_dict(ha_state)
            else:
                st.error(f"Failed to parse HA state from {panorama}.")
        else:
            st.error(f"Failed to retrieve HA state from {panorama}. Status code: {response.status_code}")

    return ha_states

def display_ha_state(primary_pan):
    panorama_instances = ['A46PANORAMA', 'L17PANORAMA']  # Replace with actual Panorama hostnames
    ha_states = get_pan_ha_state(panorama_instances)

    # Create Row Labels from the panorama instances, except we add a " <<< ACT" label for whichever instance is the primary one
    pan_labels = [f"{panorama.upper()} <<< ACT" if panorama == primary_pan else panorama.upper() for panorama in panorama_instances]
    # Write the pan_labels to a file
    pan_labels_path = "/tmp/palo/pan_labels.txt"
    with open(pan_labels_path, 'w') as file:
        file.write('\n'.join(pan_labels))

    if ha_states:
        # Write ha_states.items() to a file for debugging
        ha_states_items_path = "/tmp/palo/ha_states_items.txt"
        with open(ha_states_items_path, 'w') as file:
            for host, data in ha_states.items():
                file.write(f"Host: {host}\nData: {data}\n\n")

        # Create a list of all unique labels
        all_labels = list(set().union(*[data.keys() for data in ha_states.values()]))
        # Create a DataFrame with labels as rows and hosts as columns
        df = pd.DataFrame(index=all_labels)

        for host, data in ha_states.items():
            df[host] = pd.Series(data)

        # Fill NaN with empty strings
        df = df.fillna('')

        # Add a column for labels and perform string replacements
        df.index = df.index.str.replace('local-info/', '', regex=False)
        df.index = df.index.str.replace('/enabled', '', regex=False)
        df.insert(0, 'HA_State_Vars', df.index)

        # Sort the index: non-peer first, then peer, both alphabetically
        non_peer_index = sorted([idx for idx in df.index if "peer" not in idx])
        peer_index = sorted([idx for idx in df.index if "peer" in idx])
        sorted_index = non_peer_index + peer_index
        df = df.loc[sorted_index]

        # Define key variables and reorder them
        key_vars = ['state', 'mgmt-ip', 'mgmt-macaddr', 'priority']
        existing_keys = [key for key in key_vars if key in df.index]
        key_df = df.loc[existing_keys]             

        # Calculate the height to display all rows without scrolling
        row_height = 35  # Approximate height per row in pixels
        key_height = row_height * len(key_df)

        # Configure columns using st.column_config
        column_config = {
            "HA_State_Vars": st.column_config.TextColumn("HA_State_Vars", width=200),
            pan_labels[0]: st.column_config.TextColumn(pan_labels[0], width=200),
            pan_labels[1]: st.column_config.TextColumn(pan_labels[1], width=200)
        }

        # Display the key DataFrame using Streamlit with column configuration and custom height
        st.subheader("Key HA State Variables")
        st.dataframe(key_df.reset_index(drop=True), column_config=column_config, height=key_height)

        # Separate the remaining DataFrame into additional variables
        additional_df = df.drop(index=existing_keys)

        # Reset index for additional DataFrame
        additional_df_reset = additional_df.reset_index(drop=True)

        # Display the additional DataFrame in a collapsible section
        with st.expander("Additional HA State Variables"):
            st.dataframe(additional_df_reset, column_config=column_config, height=row_height * len(additional_df))