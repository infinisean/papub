import streamlit as st
import requests
import os
from xml.etree import ElementTree as ET
from prettytable import PrettyTable
import logging

def read_file(file_path):
    logging.debug(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    logging.debug(f"Successfully read file: {file_path}")
    return content

def parse_element(element, table, parent_tag=""):
    """Recursively parse XML elements and add them to the table."""
    for child in element:
        tag = f"{parent_tag}/{child.tag}" if parent_tag else child.tag
        if len(child):  # If the element has children, recurse
            parse_element(child, table, tag)
        else:
            table.add_row([tag, child.text])

def get_pan_ha_state(panorama_instances):
    ha_states = {}
    for panorama in panorama_instances:
        command = "<show><high-availability><state></state></high-availability></show>"
        base_dir = '/home/netmonitor/.cred'
        pankey_path = os.path.join(base_dir, 'pankey')

        # Read the Panorama API key
        if os.path.exists(pankey_path):
            panorama_api_key = read_file(pankey_path)
        else:
            st.error(f"Panorama API key file '{pankey_path}' not found.")
            return

        headers = {'X-PAN-KEY': panorama_api_key}
        url = f"https://{panorama}/api/?type=op&cmd={command}"
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            xml_response = ET.fromstring(response.text)
            ha_state = xml_response.find('.//result')
            if ha_state is not None:
                table = PrettyTable()
                table.field_names = ["Element", "Value"]
                parse_element(ha_state, table)
                ha_states[panorama] = table
            else:
                st.error(f"Failed to parse HA state from {panorama}.")
        else:
            st.error(f"Failed to retrieve HA state from {panorama}. Status code: {response.status_code}")

    return ha_states

def display_ha_state():
    panorama_instances = ['a46panorama', 'l17panorama']  # Replace with actual Panorama hostnames
    ha_states = get_pan_ha_state(panorama_instances)

    if ha_states:
        col1, col2 = st.columns(2)
        for i, (panorama, table) in enumerate(ha_states.items()):
            if i % 2 == 0:
                col1.text(f"HA State for {panorama}")
                col1.text(table)
            else:
                col2.text(f"HA State for {panorama}")
                col2.text(table)