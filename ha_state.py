import streamlit as st
import requests
import os
from xml.etree import ElementTree as ET
import pandas as pd
import logging

def read_file(file_path):
    logging.debug(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    logging.debug(f"Successfully read file: {file_path}")
    return content

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

def display_ha_state():
    panorama_instances = ['a46panorama', 'l17panorama']  # Replace with actual Panorama hostnames
    ha_states = get_pan_ha_state(panorama_instances)

    if ha_states:
        # Create a DataFrame with labels as the index
        all_labels = set()
        for data in ha_states.values():
            all_labels.update(data.keys())

        # Create a DataFrame with labels as rows and hosts as columns
        df = pd.DataFrame(index=all_labels)

        for host, data in ha_states.items():
            df[host] = pd.Series(data)

        # Fill NaN with empty strings
        df = df.fillna('')

        # Add a column for labels
        df.insert(0, 'Label', df.index)

        # Create columns in Streamlit
        col1, col2, col3 = st.columns(3)

        # Display the labels, Host A, and Host B data in separate columns
        col1.write("Labels")
        col1.write(df['Label'])

        col2.write("Host A")
        col2.write(df[panorama_instances[0]])

        col3.write("Host B")
        col3.write(df[panorama_instances[1]])
        