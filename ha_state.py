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
        # Create a list of all unique labels
        all_labels = list(set().union(*[data.keys() for data in ha_states.values()]))
        # Create a DataFrame with labels as rows and hosts as columns
        df = pd.DataFrame(index=all_labels)

        for host, data in ha_states.items():
            df[host] = pd.Series(data)

        # Fill NaN with empty strings
        df = df.fillna('')

        # Add a column for labels and perform string replacements
        #df.index = df.index.str.replace('peer-info/', '', regex=False)
        df.index = df.index.str.replace('local-info/', '', regex=False)
        df.index = df.index.str.replace('/enabled', '', regex=False)
        df.insert(0, 'HA_State_Vars', df.index)

        # Sort the index: non-peer first, then peer, both alphabetically
        non_peer_index = sorted([idx for idx in df.index if "peer" not in idx])
        peer_index = sorted([idx for idx in df.index if "peer" in idx])
        sorted_index = non_peer_index + peer_index
        df = df.loc[sorted_index]

        # Determine which columns should be CheckboxColumns
        checkbox_columns = df.columns[df.apply(lambda col: col.isin(['yes', 'no']).all())]

        # Configure columns using st.column_config
        column_config = {
            "HA_State_Vars": st.column_config.TextColumn("HA_State_Vars", width=200),
            panorama_instances[0]: st.column_config.TextColumn(panorama_instances[0], width=200),
            panorama_instances[1]: st.column_config.TextColumn(panorama_instances[1], width=200)
        }

        # Update column configuration for checkbox columns
        for col in checkbox_columns:
            column_config[col] = st.column_config.CheckboxColumn(col, readonly=True)

        # Separate the DataFrame into differing and identical rows
        differing_df = df[df[panorama_instances[0]] != df[panorama_instances[1]]]
        identical_df = df[df[panorama_instances[0]] == df[panorama_instances[1]]]

        # Calculate the height to display all rows without scrolling
        row_height = 35  # Approximate height per row in pixels
        differing_height = row_height * len(differing_df)
        identical_height = row_height * len(identical_df)

        # Display the differing DataFrame using Streamlit with column configuration and custom height
        st.subheader("Differing HA State Variables")
        st.dataframe(differing_df.reset_index(drop=True), column_config=column_config, height=differing_height)

        # Display the identical DataFrame in a collapsible section
        with st.expander("Identical HA State Variables"):
            st.dataframe(identical_df.reset_index(drop=True), column_config=column_config, height=identical_height)
        