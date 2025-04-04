import streamlit as st
import requests
from xml.etree import ElementTree as ET
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to get API key
def get_api_key(hostname, username, password):
    url = f"https://{hostname}/api/?type=keygen"
    payload = {'user': username, 'password': password}
    response = requests.post(url, data=payload, verify=False)
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        if xml_response.attrib['status'] == 'success':
            return xml_response.find('.//key').text
    return None

# Function to get system info and save raw response to a file
def get_system_info(hostname, api_key):
    url = f"https://{hostname}/api/?type=op&cmd=<show><system><info></info></system></show>"
    headers = {'X-PAN-KEY': api_key}
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        # Save raw response to a file
        with open(f"{hostname}_system_info.txt", "w") as file:
            file.write(response.text)
        return ET.fromstring(response.text)
    return None

# Streamlit app
def main():
    st.title("Palo Alto Panorama Health Dashboard")

    # Check for the existence of the "testingkey" file
    api_key = None
    if os.path.exists("testingkey"):
        with open("testingkey", "r") as file:
            api_key = file.read().strip()
        st.info("Using API key from 'testingkey' file.")
    else:
        # Prompt for user credentials
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Get API keys for both Panorama instances
            lak_api_key = get_api_key('l17panorama', username, password)
            atl_api_key = get_api_key('a46panorama', username, password)

            if lak_api_key and atl_api_key:
                st.success("Successfully obtained API keys.")
                api_key = lak_api_key  # Use one of the keys for further operations
            else:
                st.error("Failed to obtain API keys. Please check your credentials.")

    if api_key:
        # Get system info for both Panorama instances
        lak_info = get_system_info('l17panorama', api_key)
        atl_info = get_system_info('a46panorama', api_key)

        if lak_info is not None and atl_info is not None:
            # Extract relevant information
            def extract_info(system_info):
                return {
                    'Hostname': system_info.find('.//hostname').text,
                    'IP Address': system_info.find('.//ip-address').text,
                    'Uptime': system_info.find('.//uptime').text,
                    'Model': system_info.find('.//model').text,
                    'Version': system_info.find('.//sw-version').text
                }

            lak_data = extract_info(lak_info)
            atl_data = extract_info(atl_info)

            # Display the information in a table
            st.table([lak_data, atl_data])
        else:
            st.error("Failed to retrieve system information.")

if __name__ == "__main__":
    main()

